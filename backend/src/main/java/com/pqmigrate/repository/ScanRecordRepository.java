package com.pqmigrate.repository;

import com.pqmigrate.model.ScanRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ScanRecordRepository extends JpaRepository<ScanRecord, Long> {
    List<ScanRecord> findTop10ByOrderByCreatedAtDesc();
}
