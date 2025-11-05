package com.example.demo.dto;

import java.util.List;

import com.example.demo.model.Assignment;
import com.example.demo.model.StudentSubmission;
import com.example.demo.model.Testcase;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Data
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class RunRequest {
    // private String languageId;
    // private String sourceCode;
    private Assignment assignment;
    private StudentSubmission submission;
    private List<Testcase> testcase;
    // private String input;
    private Integer cputime = 10;      
    private Integer memorylimit = 2000000;  
}
