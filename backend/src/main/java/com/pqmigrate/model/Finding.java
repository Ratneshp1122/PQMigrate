package com.pqmigrate.model;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "findings")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Finding {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long scanId;

    private String primitiveName;

    private String filePath;

    private int lineNumber;

    private String role;

    private String operation;

    private String status;

    private String confidence;

    private String detectionType;

    private String targetAlgorithm;

    private String targetStandard;

    private boolean patchAvailable;

    private boolean requiresManualIntervention;

    private String interventionReason;
}
