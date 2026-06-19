import React from "react";
import { createRoot } from "react-dom/client";
import { HeroSpline } from "./hero-spline";

const heroSplineRoot = document.getElementById("hero-spline-root");

if (heroSplineRoot) {
  createRoot(heroSplineRoot).render(
    <React.StrictMode>
      <HeroSpline />
    </React.StrictMode>
  );
}
