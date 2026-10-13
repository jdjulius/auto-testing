import { defineConfig } from "allure";

export default defineConfig({
  name: "auto-testing",
  output: "reportes/allure-report",
  plugins: {
    awesome: {
      options: {
        reportName: "auto-testing",
        reportLanguage: "es",
        singleFile: true,
        groupBy: ["feature", "story"],
      },
    },
    dashboard: {
      options: {
        reportName: "auto-testing (dashboard)",
        reportLanguage: "es",
        singleFile: true,
      },
    },
  },
});
