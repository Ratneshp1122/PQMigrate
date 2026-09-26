package com.pqmigrate.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "scan_records")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ScanRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long userId;

    private String projectName;

    private String githubUrl;

    private String status; // PENDING, SCANNING, COMPLETE, FAILED

    @Lob
    private String reportJson;

    private int filesScanned;

    private int totalFindings;

    private LocalDateTime createdAt;
    
    private LocalDateTime completedAt;

    @PrePersist
    public void prePersist() {
        this.createdAt = LocalDateTime.now();
    }
}
