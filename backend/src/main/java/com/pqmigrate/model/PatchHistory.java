package com.pqmigrate.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "patch_histories")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PatchHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long findingId;

    private LocalDateTime patchedAt;

    private LocalDateTime rolledBackAt;

    private boolean testsPassed;

    @Lob
    private String patchDiff;
}
