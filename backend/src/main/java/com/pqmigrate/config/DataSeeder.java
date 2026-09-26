package com.pqmigrate.config;

import com.pqmigrate.dto.RegisterRequest;
import com.pqmigrate.service.AuthService;
import com.pqmigrate.repository.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;
import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class DataSeeder implements CommandLineRunner {
    private final AuthService authService;
    private final UserRepository userRepository;

    @Override
    public void run(String... args) {
        if (userRepository.count() == 0) {
            RegisterRequest admin = new RegisterRequest();
            admin.setEmail("admin@pqmigrate.com");
            admin.setPassword("admin123");
            authService.register(admin);
            System.out.println("Admin user seeded successfully!");
        }
    }
}
