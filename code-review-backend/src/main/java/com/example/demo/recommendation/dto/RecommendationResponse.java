package com.example.demo.recommendation.dto;

import java.util.List;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class RecommendationResponse {

    private String studentId;

    private String currentExerciseId;

    @Builder.Default
    private List<String> focusConceptIds = List.of();

    private String summary;

    @Builder.Default
    private List<RoadmapStep> roadmap = List.of();

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class RoadmapStep {
        private Integer step;
        private String summary;
        @Builder.Default
        private List<String> targetConcepts = List.of();
        @Builder.Default
        private List<RoadmapExercise> exercises = List.of();
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class RoadmapExercise {
        private Integer priority;
        private String reason;
        private Exercise exercise;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class Exercise {
        private String exerciseId;
        private String slug;
        private String title;
        private String description;
        private String content;
        private String difficulty;
        @Builder.Default
        private List<String> conceptIds = List.of();
    }
}
