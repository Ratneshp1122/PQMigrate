package com.pqmigrate.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DashboardStats {
    private long totalScans;
    private long totalFindings;
    private long criticalCount;
    private long abstentionCount;
    private long patchedCount;
    private List<String> topVulnerablePrimitives;
}
