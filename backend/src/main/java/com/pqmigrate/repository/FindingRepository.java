package com.pqmigrate.repository;

import com.pqmigrate.model.Finding;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

public interface FindingRepository extends JpaRepository<Finding, Long> {
    List<Finding> findByScanId(Long scanId);
    
    long countByConfidence(String confidence);
    long countByStatus(String status);
    
    @Query("SELECT f.primitiveName FROM Finding f GROUP BY f.primitiveName ORDER BY COUNT(f.id) DESC LIMIT 5")
    List<String> findTopVulnerablePrimitives();
}
