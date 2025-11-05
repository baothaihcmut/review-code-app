package com.example.demo.model;

import com.example.demo.dto.CodeRange;
import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReviewItem {
    @JsonProperty("line")
    private CodeRange line;
    
    @JsonProperty("column")
    private CodeRange column;   
    
    @JsonProperty("code_snippet")
    private String codeSnippet;     
    private String type;            
    private String issue;
    
    @JsonProperty("fix_suggestion")
    private String fixSuggestion;
}
