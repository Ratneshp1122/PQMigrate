package com.pqmigrate.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/patch")
@RequiredArgsConstructor
public class PatchController {

    @PostMapping("/{scanId}")
    public ResponseEntity<?> applyPatch(@PathVariable Long scanId) {
        // Placeholder for calling python patcher
        return ResponseEntity.ok(Map.of("message", "Patch applied for scan " + scanId));
    }

    @PostMapping("/{scanId}/rollback")
    public ResponseEntity<?> rollbackPatch(@PathVariable Long scanId) {
        // Placeholder for calling python rollback
        return ResponseEntity.ok(Map.of("message", "Patch rolled back for scan " + scanId));
    }
}
