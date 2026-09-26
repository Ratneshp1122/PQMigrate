package com.pqmigrate.controller;

import com.pqmigrate.dto.ScanRequest;
import com.pqmigrate.model.ScanRecord;
import com.pqmigrate.repository.FindingRepository;
import com.pqmigrate.repository.UserRepository;
import com.pqmigrate.service.ScanService;
import com.pqmigrate.service.ScannerBridge;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/scans")
@RequiredArgsConstructor
public class ScanController {

    private final ScannerBridge scannerBridge;
    private final ScanService scanService;
    private final FindingRepository findingRepository;
    private final UserRepository userRepository;

    @PostMapping
    public ResponseEntity<ScanRecord> startScan(@RequestBody ScanRequest request, Authentication authentication) {
        Long userId = currentUserId(authentication);
        ScanRecord scan = scannerBridge.runScan(request.getGithubUrl(), userId);
        return ResponseEntity.ok(scan);
    }

    @GetMapping
    public ResponseEntity<List<ScanRecord>> getAllScans(Authentication authentication) {
        return ResponseEntity.ok(scanService.getAllScans(currentUserId(authentication)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getScan(@PathVariable Long id, Authentication authentication) {
        ScanRecord scan = scanService.getScanById(id, currentUserId(authentication));
        var findings = findingRepository.findByScanId(id);
        return ResponseEntity.ok(Map.of("scan", scan, "findings", findings));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteScan(@PathVariable Long id, Authentication authentication) {
        scanService.deleteScan(id, currentUserId(authentication));
        return ResponseEntity.ok().build();
    }

    private Long currentUserId(Authentication authentication) {
        if (authentication == null || authentication.getName() == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Authentication required");
        }
        return userRepository.findByEmail(authentication.getName())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Authenticated user not found"))
                .getId();
    }
}
