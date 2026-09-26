package com.pqmigrate.service;

import com.pqmigrate.model.ScanRecord;
import com.pqmigrate.repository.FindingRepository;
import com.pqmigrate.repository.ScanRecordRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class ScannerBridgeTest {

    private final ScanRecordRepository scanRepository = mock(ScanRecordRepository.class);
    private final FindingRepository findingRepository = mock(FindingRepository.class);
    private final ScannerBridge bridge = new ScannerBridge(scanRepository, findingRepository);

    @TempDir
    Path tempDir;

    @Test
    void missingWorkerOutputCannotBecomeComplete() throws Exception {
        ScanRecord scan = ScanRecord.builder().id(1L).build();

        assertFalse(bridge.parseAndSaveResults(scan, tempDir.resolve("missing.json").toString()));
    }

    @Test
    void validWorkerOutputIsParsedAndSaved() throws Exception {
        Path report = tempDir.resolve("report.json");
        Files.writeString(report, """
                {
                  "project_name": "fixture",
                  "files_scanned": 1,
                  "total_findings": 0,
                  "records": []
                }
                """);
        ScanRecord scan = ScanRecord.builder().id(1L).build();

        assertTrue(bridge.parseAndSaveResults(scan, report.toString()));
        assertTrue(scan.getProjectName().equals("fixture"));
        verify(findingRepository).saveAll(anyList());
    }
}
