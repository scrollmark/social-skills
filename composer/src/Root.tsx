import React from "react";
import { Composition } from "remotion";
import { VideoComposition, VideoProps } from "./Video";
import { PROJECTS } from "./registry";

// One composition PER PROJECT, from the generated registry.
//
// This used to be `import defaultProps from "../props.json"` — a build-time
// import of a single global file. That made the editor single-tenant by
// construction: whoever wrote props.json last defined what every open editor
// showed, so a second agent starting work silently repointed the first agent's
// screen mid-edit. Registering one composition per project means agents pick
// their own and never contend for a shared document.
//
// Duration and dimensions still come from the props, never hardcoded.
export const RemotionRoot: React.FC = () => {
  const entries = Object.entries(PROJECTS);
  if (entries.length === 0) {
    // An empty registry means no project has been built yet. Register a stub so
    // the editor opens with an explanation instead of a blank screen.
    return (
      <Composition
        id="no-project-built"
        component={VideoComposition}
        width={1080}
        height={1920}
        fps={30}
        durationInFrames={30}
        defaultProps={{ width: 1080, height: 1920, fps: 30, scenes: [] } as VideoProps}
      />
    );
  }
  return (
    <>
      {entries.map(([id, props]) => (
        <Composition
          key={id}
          id={id}
          component={VideoComposition}
          width={props.width ?? 1080}
          height={props.height ?? 1920}
          fps={props.fps ?? 30}
          durationInFrames={1}
          defaultProps={props}
          calculateMetadata={({ props: p }) => ({
            durationInFrames: Math.max(
              1,
              p.scenes.reduce((sum, s) => sum + s.durationInFrames, 0),
            ),
            width: p.width ?? 1080,
            height: p.height ?? 1920,
            fps: p.fps ?? 30,
          })}
        />
      ))}
    </>
  );
};
