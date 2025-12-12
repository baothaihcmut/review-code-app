package com.example.demo.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.example.demo.dto.CodeReviewResponse;
import com.example.demo.dto.JobeResponse;
import com.example.demo.dto.RunRequest;
import com.example.demo.dto.RunResponse;
import com.example.demo.dto.TestcaseResult;
import com.example.demo.model.Testcase;

import lombok.extern.slf4j.Slf4j;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class JobeService {

    @Value("${jobe.base-url}")
    private String jobeBaseUrl;

    @Value("${review.url}")
    private String reviewUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    public String getLanguages() {
        String url = jobeBaseUrl + "/languages";
        return restTemplate.getForObject(url, String.class);
    }

    public RunResponse runCode(RunRequest runRequest) {
        String url = jobeBaseUrl + "/runs";
        String errorMessage = "";

        String template = loadTemplate(runRequest.getAssignment().getLanguage());

        String fullCode = template.replace(
            "// STUDENT_CODE_HERE",
            runRequest.getSubmission().getCode()
        );

        List<TestcaseResult> results = new ArrayList<>();

        if (runRequest.getTestcase() == null || runRequest.getTestcase().isEmpty()) {
            return new RunResponse(runRequest.getAssignment(), runRequest.getSubmission(), results, errorMessage);
        }

        for (Testcase testcase : runRequest.getTestcase()) {    
            String input = testcase.getInput() == null ? "" : testcase.getInput();
            
            Map<String, Object> body = Map.of(
                "run_spec", Map.of(
                    "language_id", runRequest.getAssignment().getLanguage(),
                    "sourcecode", fullCode,
                    "input", input,
                    "parameters", Map.of(
                        "cputime", runRequest.getCputime() != null ? runRequest.getCputime() : 2,
                        "memorylimit", runRequest.getMemorylimit() != null ? runRequest.getMemorylimit() : 500000
                    )
                )
            );

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);

            ResponseEntity<JobeResponse> response = restTemplate.postForEntity(url, request, JobeResponse.class);
            JobeResponse jobeResponse = response.getBody();

            log.info(jobeResponse.toString());

            errorMessage = jobeResponse != null ? jobeResponse.getCmpinfo() : "";
            String actualOutput = jobeResponse != null ? jobeResponse.getStdout() : "";
            String expectedOutput = testcase.getExpect() == null ? "" : testcase.getExpect();

            String normActual = normalize(actualOutput);
            String normExpected = normalize(expectedOutput);

            boolean passed = normActual.equals(normExpected);
            TestcaseResult.TestcaseStatus status = passed ? TestcaseResult.TestcaseStatus.PASSED : TestcaseResult.TestcaseStatus.FAILED;
            
            results.add(
                new TestcaseResult(
                    testcase.getName(),
                    status,
                    input,
                    expectedOutput,
                    actualOutput
                )
            );
        }
        // Map<String, Object> body = Map.of(
        //         "run_spec", Map.of(
        //             "language_id", runRequest.getAssignment().getLanguage(),
        //             "sourcecode", runRequest.getSubmission().getCode(),
        //             "input", runRequest.getTestcase().getInput() == null ? "" : runRequest.getTestcase().getInput(),
        //             "parameters", Map.of(
        //                 "cputime", runRequest.getCputime() != null ? runRequest.getCputime() : 2,
        //                 "memorylimit", runRequest.getMemorylimit() != null ? runRequest.getMemorylimit() : 500000
        //             )
        //         )
        //     );
        // ResponseEntity<JobeResponse> response = restTemplate.postForEntity(url, request, JobeResponse.class);
        // return response.getBody();

        return new RunResponse(runRequest.getAssignment(), runRequest.getSubmission(), results, errorMessage);
    }


    private String normalize(String s) {
        if (s == null) return "";
        // trim trailing/leading whitespace and unify newlines
        return s.replace("\r\n", "\n").trim();
    }

    private String loadTemplate(String language) {
        try {
            String filename;
            switch (language.toLowerCase()) {
                case "java" -> filename = "templates/java_template.txt";
                case "python" -> filename = "templates/python_template.txt";
                default -> filename = "templates/cpp_template.txt";
            }

            ClassPathResource resource = new ClassPathResource(filename);

            try (InputStream inputStream = resource.getInputStream()) {
                return new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
            }

        } catch (Exception e) {
            log.error("Cannot load template for language: {}", language, e);
            return "";
        }
    }


    // private String loadTemplate(String language) {
    //     try {
    //         String filename;
    //         switch (language.toLowerCase()) {
    //             case "java": filename = "templates/java_template.txt"; break;
    //             case "python": filename = "templates/python_template.txt"; break;
    //             default: filename = "templates/cpp_template.txt";
    //         }
    //         var resource = new ClassPathResource(filename);
    //         return Files.readString(resource.getFile().toPath(), StandardCharsets.UTF_8);
    //     } catch (Exception e) {
    //         log.error("Cannot load template for language: {}", language, e);
    //         return "";
    //     }
    // }


    public CodeReviewResponse reviewCode(RunRequest runRequest) {

        RunResponse runResponse = runCode(runRequest);

        Map<String, Object> body = Map.of(
            "assignment", runRequest.getAssignment(),
            "student_submission", runRequest.getSubmission(),
            "test_results", runResponse.getTestcaseResults()
        );

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);

        ResponseEntity<CodeReviewResponse> response = restTemplate.postForEntity(reviewUrl, request, CodeReviewResponse.class);
        log.info("Review response: {}", response.getBody());
        return response.getBody();
    }


}
