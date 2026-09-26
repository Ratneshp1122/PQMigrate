package com.pqmigrate.repository;

import com.pqmigrate.model.ScanRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface ScanRecordRepository extends JpaRepository<ScanRecord, Long> {
    List<ScanRecord> findTop10ByOrderByCreatedAtDesc();
    List<ScanRecord> findByUserIdOrderByCreatedAtDesc(Long userId);
    Optional<ScanRecord> findByIdAndUserId(Long id, Long userId);
}
