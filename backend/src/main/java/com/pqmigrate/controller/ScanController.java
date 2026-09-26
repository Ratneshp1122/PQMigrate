package com.pqmigrate.controller;

import com.pqmigrate.dto.ScanRequest;
import com.pqmigrate.model.ScanRecord;
import com.pqmigrate.repository.FindingRepository;
import com.pqmigrate.service.ScanService;
import com.pqmigrate.service.ScannerBridge;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/scans")
@RequiredArgsConstructor
public class ScanController {

    private final ScannerBridge scannerBridge;
    private final ScanService scanService;
    private final FindingRepository findingRepository;

    @PostMapping
    public ResponseEntity<ScanRecord> startScan(@RequestBody ScanRequest request) {
        // Simple placeholder for userId (could get from auth context)
        Long userId = 1L;
        ScanRecord scan = scannerBridge.runScan(request.getGithubUrl(), userId);
        return ResponseEntity.ok(scan);
    }

    @GetMapping
    public ResponseEntity<List<ScanRecord>> getAllScans() {
        return ResponseEntity.ok(scanService.getAllScans());
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getScan(@PathVariable Long id) {
        ScanRecord scan = scanService.getScanById(id);
        var findings = findingRepository.findByScanId(id);
        return ResponseEntity.ok(Map.of("scan", scan, "findings", findings));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteScan(@PathVariable Long id) {
        scanService.deleteScan(id);
        return ResponseEntity.ok().build();
    }
}
