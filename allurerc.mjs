import { defineConfig } from "allure";

export default defineConfig({
  name: "auto-testing · saucedemo",
  output: "reportes/allure-report",
  plugins: {
    awesome: {
      options: {
        reportName: "auto-testing · saucedemo",
        reportLanguage: "es",
        singleFile: true,
        groupBy: ["feature", "story"],
      },
    },
    dashboard: {
      options: {
        reportName: "auto-testing · saucedemo (dashboard)",
        reportLanguage: "es",
        singleFile: true,
      },
    },
  },
});
