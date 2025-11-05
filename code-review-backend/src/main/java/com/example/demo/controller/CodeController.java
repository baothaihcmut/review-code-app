package com.example.demo.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import com.example.demo.dto.CodeReviewResponse;
import com.example.demo.dto.RunRequest;
import com.example.demo.dto.RunResponse;
import com.example.demo.service.JobeService;

@RestController
@RequestMapping("/api")
@CrossOrigin("*")
public class CodeController {

    @Autowired
    private JobeService jobeService;

    @GetMapping("/languages")
    public String getLanguages() {
        return jobeService.getLanguages();
    }

    @PostMapping("/run")
    public RunResponse runCode(@RequestBody RunRequest request) {
        return jobeService.runCode(
                request
        );
    }

    @PostMapping("/review")
    public CodeReviewResponse reviewCode(@RequestBody RunRequest request) {
        return jobeService.reviewCode(
                request
        );
    }
}
