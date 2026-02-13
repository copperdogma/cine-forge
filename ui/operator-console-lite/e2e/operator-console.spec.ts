import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  let knownProjects = [
    {
      project_id: "proj-1",
      display_name: "project-ui",
      project_path: "output/project-ui",
      artifact_groups: 3,
      run_count: 2,
    },
  ];

  await page.route("**/api/**", async (route) => {
    const url = route.request().url();
    const method = route.request().method();

    if (url.endsWith("/api/projects/recent") && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(knownProjects),
      });
      return;
    }

    if (url.endsWith("/api/projects/new") && method === "POST") {
      knownProjects = [
        {
          project_id: "proj-1",
          display_name: "project-ui",
          project_path: "output/project-ui",
          artifact_groups: 0,
          run_count: 0,
        },
      ];
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          project_id: "proj-1",
          display_name: "project-ui",
          artifact_groups: 0,
          run_count: 0,
        }),
      });
      return;
    }

    if (url.endsWith("/api/projects/proj-1/inputs/upload") && method === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          original_name: "sample.fountain",
          stored_path: "output/project-ui/inputs/uploaded_sample.fountain",
          size_bytes: 128,
        }),
      });
      return;
    }

    if (url.endsWith("/api/projects/open") && method === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          project_id: "proj-1",
          display_name: "project-ui",
          artifact_groups: 3,
          run_count: 2,
        }),
      });
      return;
    }

    if (url.endsWith("/api/runs/start") && method === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ run_id: "run-ui-001" }),
      });
      return;
    }

    if (url.includes("/api/runs/run-ui-001/state") && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          run_id: "run-ui-001",
          state: {
            run_id: "run-ui-001",
            recipe_id: "mvp_ingest",
            stages: {
              ingest: { status: "done", duration_seconds: 0.1, cost_usd: 0, artifact_refs: [] },
              normalize: { status: "done", duration_seconds: 0.1, cost_usd: 0, artifact_refs: [] },
              extract_scenes: {
                status: "done",
                duration_seconds: 0.1,
                cost_usd: 0,
                artifact_refs: [],
              },
              project_config: {
                status: "paused",
                duration_seconds: 0.1,
                cost_usd: 0,
                artifact_refs: [],
              },
            },
            total_cost_usd: 0,
          },
          background_error: null,
        }),
      });
      return;
    }

    if (url.includes("/api/projects/proj-1/artifacts") && method === "GET") {
      if (url.endsWith("/artifacts")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              artifact_type: "draft_project_config",
              entity_id: "project",
              latest_version: 1,
              health: "needs_review",
            },
          ]),
        });
        return;
      }
      if (url.endsWith("/artifacts/draft_project_config/project")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              artifact_type: "draft_project_config",
              entity_id: "project",
              version: 1,
              health: "needs_review",
              path: "artifacts/draft_project_config/project/v1.json",
            },
          ]),
        });
        return;
      }
      if (url.endsWith("/artifacts/draft_project_config/project/1")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            artifact_type: "draft_project_config",
            entity_id: "project",
            version: 1,
            payload: {
              data: {
                title: "Draft Title",
                format: "feature",
                tone: ["tense"],
                genre: ["thriller"],
              },
            },
          }),
        });
        return;
      }
    }

    if (url.endsWith("/api/projects/proj-1/runs") && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{ run_id: "run-ui-001", status: "done" }]),
      });
      return;
    }

    if (url.includes("/api/runs/run-ui-001/events") && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ run_id: "run-ui-001", events: [{ event: "stage_started" }] }),
      });
      return;
    }

    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ code: "not_mocked", message: `No mock for ${method} ${url}` }),
    });
  });
});

test("file-first onboarding and project switcher flow", async ({ page }) => {
  await page.goto("/new");
  await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible();

  const picker = page.locator('input[type="file"]');
  await picker.setInputFiles({
    name: "sample.fountain",
    mimeType: "text/plain",
    buffer: Buffer.from("INT. OFFICE - DAY\n"),
  });

  await page.getByRole("button", { name: "Create Project From File" }).click();

  await expect(page.getByRole("heading", { name: "Run Pipeline" })).toBeVisible();
  await expect(page.getByText("Active project:")).toContainText("project-ui");

  await page.getByLabel("Config Confirmation Mode").selectOption("review");
  await page.getByRole("button", { name: "Start Run" }).click();
  await expect(page.getByText("Draft Project Config Review")).toBeVisible();

  await page.goto("/artifacts");
  await page.getByRole("button", { name: "Refresh Artifact Groups" }).click();
  await expect(page.getByText("draft_project_config/project v1")).toBeVisible();

  await page.getByRole("button", { name: "Projects" }).click();
  await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible();
});
