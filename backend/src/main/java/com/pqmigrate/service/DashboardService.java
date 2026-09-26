package com.pqmigrate.service;

import com.pqmigrate.dto.DashboardStats;
import com.pqmigrate.model.ScanRecord;
import com.pqmigrate.repository.FindingRepository;
import com.pqmigrate.repository.PatchHistoryRepository;
import com.pqmigrate.repository.ScanRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class DashboardService {

    private final ScanRecordRepository scanRecordRepository;
    private final FindingRepository findingRepository;
    private final PatchHistoryRepository patchHistoryRepository;

    public DashboardStats getStats() {
        long totalScans = scanRecordRepository.count();
        long totalFindings = findingRepository.count();
        long criticalCount = findingRepository.countByConfidence("HIGH");
        long abstentionCount = findingRepository.countByStatus("VULNERABLE");
        long patchedCount = patchHistoryRepository.count();
        List<String> topVulnerablePrimitives = findingRepository.findTopVulnerablePrimitives();

        return DashboardStats.builder()
                .totalScans(totalScans)
                .totalFindings(totalFindings)
                .criticalCount(criticalCount)
                .abstentionCount(abstentionCount)
                .patchedCount(patchedCount)
                .topVulnerablePrimitives(topVulnerablePrimitives)
                .build();
    }

    public List<ScanRecord> getRecentScans() {
        return scanRecordRepository.findTop10ByOrderByCreatedAtDesc();
    }
}
