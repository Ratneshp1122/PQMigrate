package com.pqmigrate.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.pqmigrate.model.Finding;
import com.pqmigrate.model.ScanRecord;
import com.pqmigrate.repository.FindingRepository;
import com.pqmigrate.repository.ScanRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class ScannerBridge {

    private final ScanRecordRepository scanRecordRepository;
    private final FindingRepository findingRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${scanner.python.path}")
    private String scannerPath;

    @Value("${scanner.python.venv}")
    private String venvPython;

    public ScanRecord runScan(String githubUrl, Long userId) {
        ScanRecord scan = ScanRecord.builder()
                .userId(userId)
                .githubUrl(githubUrl)
                .status("SCANNING")
                .projectName(githubUrl.substring(githubUrl.lastIndexOf('/') + 1))
                .build();
        scan = scanRecordRepository.save(scan);

        String scanId = UUID.randomUUID().toString();
        String outputPath = "/tmp/scan_" + scanId + ".json";

        try {
            ProcessBuilder pb = new ProcessBuilder(
                    venvPython,
                    scannerPath + "/cli.py",
                    "repo",
                    githubUrl,
                    "--format", "json",
                    "--output", outputPath
            );
            pb.redirectErrorStream(true);
            Process process = pb.start();
            boolean finished = process.waitFor(5, TimeUnit.MINUTES);

            if (finished && (process.exitValue() == 0 || process.exitValue() == 1)) {
                parseAndSaveResults(scan, outputPath);
                scan.setStatus("COMPLETE");
            } else {
                scan.setStatus("FAILED");
            }
        } catch (Exception e) {
            scan.setStatus("FAILED");
        }

        scan.setCompletedAt(LocalDateTime.now());
        return scanRecordRepository.save(scan);
    }

    private void parseAndSaveResults(ScanRecord scan, String outputPath) throws IOException {
        File resultFile = new File(outputPath);
        if (!resultFile.exists()) return;

        JsonNode rootNode = objectMapper.readTree(resultFile);
        
        scan.setProjectName(rootNode.path("project_name").asText());
        scan.setFilesScanned(rootNode.path("files_scanned").asInt());
        scan.setTotalFindings(rootNode.path("total_findings").asInt());
        scan.setReportJson(rootNode.toString());

        JsonNode records = rootNode.path("records");
        List<Finding> findings = new ArrayList<>();
        if (records.isArray()) {
            for (JsonNode node : records) {
                JsonNode findingNode = node.path("finding");
                JsonNode locationNode = findingNode.path("location");
                JsonNode planNode = node.path("plan");
                
                Finding f = Finding.builder()
                        .scanId(scan.getId())
                        .primitiveName(findingNode.path("primitive_name").asText())
                        .filePath(locationNode.path("file_path").asText())
                        .lineNumber(locationNode.path("line_number").asInt())
                        .role(findingNode.path("role").asText())
                        .operation(findingNode.path("operation").asText())
                        .status(findingNode.path("status").asText())
                        .confidence(findingNode.path("confidence").asText())
                        .detectionType(findingNode.path("detection_type").asText())
                        .targetAlgorithm(planNode.path("target_algorithm").asText())
                        .targetStandard(planNode.path("target_standard").asText())
                        .patchAvailable(planNode.path("patch_available").asBoolean())
                        .requiresManualIntervention(planNode.path("requires_manual_intervention").asBoolean())
                        .interventionReason(planNode.path("intervention_reason").asText())
                        .build();
                findings.add(f);
            }
        }
        findingRepository.saveAll(findings);
    }
}
