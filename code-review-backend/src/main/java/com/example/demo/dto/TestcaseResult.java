package com.example.demo.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TestcaseResult {
    private String name;
    private TestcaseStatus status;
    private String input;
    private String expect;
    private String actual;
    // private String errorMessage;

    public enum TestcaseStatus {
        PASSED,
        FAILED
    }
}
