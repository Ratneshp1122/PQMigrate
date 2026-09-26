package com.pqmigrate.controller;

import com.pqmigrate.dto.DashboardStats;
import com.pqmigrate.model.ScanRecord;
import com.pqmigrate.service.DashboardService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/dashboard")
@RequiredArgsConstructor
public class DashboardController {

    private final DashboardService dashboardService;

    @GetMapping("/stats")
    public ResponseEntity<DashboardStats> getStats() {
        return ResponseEntity.ok(dashboardService.getStats());
    }

    @GetMapping("/recent")
    public ResponseEntity<List<ScanRecord>> getRecentScans() {
        return ResponseEntity.ok(dashboardService.getRecentScans());
    }
}
