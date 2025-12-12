package com.example.demo.dto;

import java.util.List;

import com.example.demo.model.Assignment;
import com.example.demo.model.StudentSubmission;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RunResponse {
    private Assignment assignment;
    private StudentSubmission submission;
    private List<TestcaseResult> testcaseResults;
    private String errorMessage;
}
