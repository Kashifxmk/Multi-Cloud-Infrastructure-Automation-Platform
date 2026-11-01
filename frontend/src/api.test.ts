import { afterEach, describe, expect, it, vi } from "vitest";
import { getDashboard } from "./api";


describe("frontend API client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("requests dashboard data with browser credentials", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          mode: "demo",
          message: "demo",
          metrics: { cloud_accounts: 0, deployments: 0, active_resources: 0, monthly_spend: null },
          provider_distribution: [],
          recent_activity: [],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await getDashboard();

    expect(result.mode).toBe("demo");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/dashboard"),
      expect.objectContaining({ credentials: "include" }),
    );
  });
});
