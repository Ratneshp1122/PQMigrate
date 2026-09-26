package com.pqmigrate.service;

import com.pqmigrate.model.ScanRecord;
import com.pqmigrate.repository.ScanRecordRepository;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class ScanServiceTest {

    private final ScanRecordRepository repository = mock(ScanRecordRepository.class);
    private final ScanService service = new ScanService(repository);

    @Test
    void listsOnlyAuthenticatedUsersScans() {
        ScanRecord owned = ScanRecord.builder().id(10L).userId(7L).build();
        when(repository.findByUserIdOrderByCreatedAtDesc(7L)).thenReturn(List.of(owned));

        assertEquals(List.of(owned), service.getAllScans(7L));
    }

    @Test
    void rejectsScanOwnedByAnotherUserAsNotFound() {
        when(repository.findByIdAndUserId(10L, 7L)).thenReturn(Optional.empty());

        assertThrows(ResponseStatusException.class, () -> service.getScanById(10L, 7L));
    }

    @Test
    void deletesOnlyRecordResolvedWithOwner() {
        ScanRecord owned = ScanRecord.builder().id(10L).userId(7L).build();
        when(repository.findByIdAndUserId(10L, 7L)).thenReturn(Optional.of(owned));

        service.deleteScan(10L, 7L);

        verify(repository).delete(owned);
    }
}
