package com.example.demo.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Testcase {
    // private Long id;
    private String name;
    // private Assignment assignment;
    private String input;
    private String expect;
}
