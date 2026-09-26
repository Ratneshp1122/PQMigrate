package com.pqmigrate.repository;

import com.pqmigrate.model.PatchHistory;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PatchHistoryRepository extends JpaRepository<PatchHistory, Long> {
}
