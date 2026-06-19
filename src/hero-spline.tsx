import { SplineScene } from "./components/ui/spline-scene";

// Coller ici l'URL .splinecode de la scene Spline basket MBC.
const MBC_SPLINE_SCENE_URL = "https://prod.spline.design/KHuEbIVgmKJCZVLk/scene.splinecode";

export function HeroSpline() {
  if (!MBC_SPLINE_SCENE_URL) return null;

  return (
    <div className="hero-spline-react" aria-hidden="true">
      <SplineScene scene={MBC_SPLINE_SCENE_URL} className="hero-spline-canvas" />
    </div>
  );
}
