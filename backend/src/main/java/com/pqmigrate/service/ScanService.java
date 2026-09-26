package com.pqmigrate.service;

import com.pqmigrate.model.ScanRecord;
import com.pqmigrate.repository.ScanRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ScanService {

    private final ScanRecordRepository scanRecordRepository;

    public List<ScanRecord> getAllScans(Long userId) {
        return scanRecordRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    public ScanRecord getScanById(Long id, Long userId) {
        return scanRecordRepository.findByIdAndUserId(id, userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Scan not found"));
    }

    public void deleteScan(Long id, Long userId) {
        ScanRecord ownedScan = getScanById(id, userId);
        scanRecordRepository.delete(ownedScan);
    }
}
