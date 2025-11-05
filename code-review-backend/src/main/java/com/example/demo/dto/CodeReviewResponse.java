package com.example.demo.dto;

import java.util.List;

import com.example.demo.model.ReviewItem;
import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CodeReviewResponse {
 private String summary;
 private String detail;

 @JsonProperty("review_items")
 private List<ReviewItem> reviewItems;
}
