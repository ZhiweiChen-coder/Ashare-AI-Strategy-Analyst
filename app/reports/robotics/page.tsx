import type { Metadata } from "next";
import { RoboticsReportClient } from "./robotics-report-client";

export const metadata: Metadata = {
  title: "Robotics industry research report | OpenAshare",
  description: "An archived industry research report covering company fundamentals, price action, news, and risk context.",
};

export default function RoboticsReportPage() {
  return <RoboticsReportClient />;
}
