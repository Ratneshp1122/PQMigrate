package com.pqmigrate.service;

import com.pqmigrate.model.ScanRecord;
import com.pqmigrate.repository.ScanRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ScanService {

    private final ScanRecordRepository scanRecordRepository;

    public List<ScanRecord> getAllScans() {
        return scanRecordRepository.findAll();
    }

    public ScanRecord getScanById(Long id) {
        return scanRecordRepository.findById(id).orElseThrow(() -> new RuntimeException("Scan not found"));
    }

    public void deleteScan(Long id) {
        scanRecordRepository.deleteById(id);
    }
}
