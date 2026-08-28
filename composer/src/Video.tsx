import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  Loop,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// [x, y, w, h] as fractions of the canvas — same convention as the
// storyboard schema (and showrunner's composite rects before it).
export type Rect = [number, number, number, number];

export type Layer = {
  id: string;
  type: "video" | "image" | "placeholder" | "card" | "effect";
  /** Path under composer/public/ for video/image layers. */
  src?: string;
  /** Placeholder label + fill, e.g. "HOST" on a slate blue box. */
  label?: string;
  color?: string;
  /** Card layers: live, editable typography — no baked images. */
  heading?: string;
  subtext?: string;
  /** Equal-weight monospace rows, for readouts where no line is the title
   * (coordinates, key/value pairs). Takes precedence over heading/subtext. */
  lines?: string[];
  bg?: string;
  fg?: string;
  rect?: Rect;
  /** Ease from this rect to `rect`, holding at `from` for `delay` seconds first. */
  enter?: { from: Rect; seconds: number; delay?: number };
  /** Ease from `rect` back to this rect, finishing at scene end. */
  exit?: { to: Rect; seconds: number };
  fit?: "cover" | "contain";
  /** Repeat the clip when it is shorter than the scene. Requires
   * `srcDurationInFrames` (build_props.py probes it) — OffthreadVideo has no
   * `loop` prop of its own, so this is implemented with <Loop>. */
  loop?: boolean;
  srcDurationInFrames?: number;
  muted?: boolean;
  /** Visibility window within the scene, ms (for popups pinned to moments —
   * e.g. images appearing where/when a presenter points). */
  atMs?: number;
  untilMs?: number;
  /** Pop-in (back-eased scale) on appear; slight shrink-fade on disappear. */
  pop?: boolean;
  /** Opacity fade, seconds. Quieter than `pop` — for title and end cards,
   * where a bounce reads as cheap and a fade reads as considered. */
  fade?: { in?: number; out?: number };
  /** Card: a third, quiet line under the subtext — URLs, dates, fine print.
   * Keeps the tagline from having to share a line with a web address. */
  footnote?: string;
  /** Card: letter-spacing on the heading, em. Small positive values make a
   * short all-caps wordmark read as a wordmark rather than a shout. */
  tracking?: number;
  /** Card: explicit heading size in px for title-forward videos. */
  fontSize?: number;
  /** Card: drop the rounded corner and the drop shadow, so the type sits on
   * the frame rather than on a panel. Cards always draw a shadow otherwise,
   * which is why a `bg` of "transparent" leaves a floating grey rectangle
   * instead of nothing. This is the switch for type set INTO flat artwork
   * (see formats/boil.md). Defaults false — existing videos are untouched. */
  flat?: boolean;
  /** Ken Burns drift across the WHOLE scene — the thing that makes a still
   * photo read as footage. `amount` is the scale delta (default 0.12). When
   * `pan` is set we hold extra scale in reserve so the crop never exposes an
   * edge mid-move. */
  ken?: { zoom?: "in" | "out"; pan?: "left" | "right" | "up" | "down"; amount?: number };
  effect?: "grain" | "breath" | "lightLeak" | "clock" | "glow" | "vignette";
  intensity?: number;
  palette?: string[];
};

export type CaptionWord = { text: string; startMs: number; endMs: number };

export type Overlay = {
  type: "title" | "stat" | "label" | "cta";
  text: string;
  position?: "top" | "center" | "bottom";
  /** Multiply the type size — for beats where a number should hit harder. */
  scale?: number;
};

export type Scene = {
  id: string;
  durationInFrames: number;
  /** Narration WAV under public/, already measured — it IS the clock. */
  audio?: string;
  captions?: CaptionWord[];
  /** Per-scene overrides merged over the video-level captionStyle. */
  captionStyle?: VideoProps["captionStyle"];
  overlays?: Overlay[];
  layers: Layer[];
};

export type VideoProps = {
  width?: number;
  height?: number;
  fps?: number;
  scenes: Scene[];
  music?: {
    src: string;
    /** Flat level, used when no envelope is present. */
    volume?: number;
    /** Per-frame music level, one entry per composition frame, written by
     * `video-studio duck_music` after build_props. When present it wins over
     * `volume`: the bed drops under narration and returns in the gaps.
     *
     * Indexed by ABSOLUTE composition frame, which is why this <Audio> lives
     * above the scene <Sequence>s — inside one, Remotion would hand the volume
     * callback a scene-relative frame and the ducking would follow the wrong
     * scene without erroring. */
    envelope?: number[];
    /** The level the envelope returns to in silence. Kept for reference; the
     * envelope already encodes it. */
    baseVolume?: number;
  };
  captionStyle?: {
    color?: string;
    highlight?: string;
    fontFamily?: string;
    /** Cycle a colour per word instead of one flat colour. Overrides `color`. */
    palette?: string[];
    /** Outline — needed once words are bright and sit on busy footage. */
    stroke?: string;
    strokeWidth?: number;
    fontSize?: number;
    /** Active word pops to this multiple of its size. 1 = off. */
    bounce?: number;
    /** Per-word tilt in degrees, alternating sign. 0 = off. */
    wiggle?: number;
    uppercase?: boolean;
    /** Distance above the bottom edge, as a fraction of height. Default 0.12.
     *  Raise it when foreground art occupies the lower frame. */
    bottom?: number;
    /** Words shown at once. Default 4 — drop to 3 for big/uppercase type,
     *  which otherwise overruns the frame width. */
    wordsPerPage?: number;
    /** Gap between words, em. Default 0.18. A thick `stroke` grows each word's
     *  visual box, so outlined type needs a wider gap or the words merge. */
    wordGap?: number;
  };
};

const FULL: Rect = [0, 0, 1, 1];

/** Smoothstep-eased rect at time t (seconds into the scene). */
const rectAt = (layer: Layer, t: number, sceneSeconds: number): Rect => {
  const rest = layer.rect ?? FULL;
  const lerp = (a: Rect, b: Rect, p: number): Rect => {
    const e = interpolate(p, [0, 1], [0, 1], {
      easing: Easing.inOut(Easing.ease),
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    return a.map((v, i) => v + (b[i] - v) * e) as Rect;
  };
  if (layer.enter) {
    const delay = layer.enter.delay ?? 0;
    if (t < delay) return layer.enter.from;
    if (t < delay + layer.enter.seconds) {
      return lerp(layer.enter.from, rest, (t - delay) / layer.enter.seconds);
    }
  }
  if (layer.exit && t > sceneSeconds - layer.exit.seconds) {
    return lerp(rest, layer.exit.to, (t - (sceneSeconds - layer.exit.seconds)) / layer.exit.seconds);
  }
  return rest;
};

const LayerView: React.FC<{ layer: Layer; sceneSeconds: number }> = ({ layer, sceneSeconds }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const ms = t * 1000;

  // Timed visibility window (popup layers).
  const atMs = layer.atMs ?? 0;
  const untilMs = layer.untilMs ?? Infinity;
  if (ms < atMs || ms >= untilMs) return null;

  // Pop-in / pop-out scaling around the visibility window.
  let popScale = 1;
  if (layer.pop) {
    const appear = interpolate(ms - atMs, [0, 300], [0, 1], {
      easing: Easing.out(Easing.back(1.7)),
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    const vanish = Number.isFinite(untilMs)
      ? interpolate(ms, [untilMs - 200, untilMs], [1, 0.6], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 1;
    popScale = appear * vanish;
  }

  // Opacity fade, measured from the layer's own visible window so it works
  // whether or not the layer is time-gated.
  let fadeOpacity = 1;
  if (layer.fade) {
    const localMs = ms - atMs;
    const endMs = Number.isFinite(untilMs) ? untilMs : sceneSeconds * 1000;
    if (layer.fade.in) {
      fadeOpacity *= interpolate(localMs, [0, layer.fade.in * 1000], [0, 1], {
        easing: Easing.out(Easing.cubic),
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
    }
    if (layer.fade.out) {
      fadeOpacity *= interpolate(ms, [endMs - layer.fade.out * 1000, endMs], [1, 0], {
        easing: Easing.in(Easing.cubic),
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
    }
  }

  const [x, y, w, h] = rectAt(layer, t, sceneSeconds);
  const style: React.CSSProperties = {
    position: "absolute",
    left: x * width,
    top: y * height,
    width: w * width,
    height: h * height,
    overflow: "hidden",
    ...(layer.pop
      ? {
          transform: `scale(${popScale})`,
          opacity: Math.min(1, popScale * 1.4) * fadeOpacity,
          borderRadius: 24,
          boxShadow: "0 10px 40px rgba(0,0,0,0.5)",
        }
      : layer.fade
        ? { opacity: fadeOpacity }
        : {}),
  };
  if (layer.type === "effect") {
    const p = Math.min(1, Math.max(0, t / Math.max(0.001, sceneSeconds)));
    const intensity = layer.intensity ?? 1;
    const colours = layer.palette ?? ["#facc15", "#fb7185", "#38bdf8"];
    if (layer.effect === "breath") {
      return (
        <div style={{ ...style, pointerEvents: "none", mixBlendMode: "screen" }}>
          {Array.from({ length: 7 }, (_, i) => {
            const phase = (p * 1.7 + i * 0.137) % 1;
            const drift = interpolate(phase, [0, 1], [0, -210 - i * 8]);
            const spread = interpolate(phase, [0, 1], [0, 130 + i * 12]);
            const opacity = Math.sin(Math.PI * phase) * 0.22 * intensity;
            return (
              <div
                key={i}
                style={{
                  position: "absolute",
                  left: `${24 + i * 7}%`,
                  bottom: `${10 + (i % 3) * 5}%`,
                  width: 150 + i * 18,
                  height: 72 + i * 12,
                  borderRadius: "50%",
                  background: "rgba(230,245,255,0.65)",
                  filter: "blur(28px)",
                  opacity,
                  transform: `translate(${spread}px, ${drift}px) scale(${0.6 + phase * 1.8})`,
                }}
              />
            );
          })}
        </div>
      );
    }
    if (layer.effect === "lightLeak") {
      const lightX = interpolate(Math.sin(p * Math.PI * 2), [-1, 1], [-18, 86]);
      return (
        <div
          style={{
            ...style,
            pointerEvents: "none",
            opacity: 0.32 * intensity,
            mixBlendMode: "screen",
            background:
              `radial-gradient(circle at ${lightX}% 18%, ${colours[0]} 0%, transparent 28%), ` +
              `linear-gradient(115deg, transparent 0%, ${colours[1]}33 42%, transparent 72%)`,
            filter: "blur(10px)",
          }}
        />
      );
    }
    if (layer.effect === "clock") {
      const secondsLeft = Math.max(0, Math.ceil(sceneSeconds - t));
      const flash = interpolate(Math.sin(p * Math.PI * 8), [-1, 1], [0.15, 0.7]);
      return (
        <div
          style={{
            ...style,
            pointerEvents: "none",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: colours[0],
            opacity: flash * intensity,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            fontSize: Math.min(width * 0.38, height * 0.22),
            fontWeight: 900,
            textShadow: `0 0 32px ${colours[0]}, 0 0 80px rgba(0,0,0,0.9)`,
          }}
        >
          05:{String(secondsLeft).padStart(2, "0")}
        </div>
      );
    }
    if (layer.effect === "glow") {
      const pulse = interpolate(Math.sin(p * Math.PI * 6), [-1, 1], [0.65, 1]);
      return (
        <div
          style={{
            ...style,
            pointerEvents: "none",
            opacity: 0.55 * pulse * intensity,
            mixBlendMode: "screen",
            background:
              `radial-gradient(circle at 50% 54%, ${colours[0]} 0%, ${colours[1]}55 18%, transparent 52%)`,
            filter: "blur(18px)",
          }}
        />
      );
    }
    if (layer.effect === "vignette") {
      return (
        <div
          style={{
            ...style,
            pointerEvents: "none",
            opacity: 0.9 * intensity,
            background:
              "radial-gradient(circle at 50% 44%, transparent 0%, transparent 42%, rgba(0,0,0,0.72) 100%)",
          }}
        />
      );
    }
    return (
      <div
        style={{
          ...style,
          pointerEvents: "none",
          opacity: 0.12 * intensity,
          mixBlendMode: "overlay",
          backgroundImage:
            "repeating-radial-gradient(circle at 18% 22%, rgba(255,255,255,0.9) 0 1px, transparent 1px 4px)",
          transform: `translate(${Math.sin(frame * 0.73) * 4}px, ${Math.cos(frame * 0.59) * 4}px)`,
        }}
      />
    );
  }
  if (layer.type === "card") {
    const boxW = w * width;
    const boxH = h * height;
    // Height alone can't size the type: the same card markup serves a small
    // popup AND a full-frame text beat, where boxH * 0.3 would be a 500px+
    // heading that overflows the canvas. Cap by height, then by the width the
    // string actually needs (~0.6em per character for this weight).
    const short = Math.min(boxW, boxH);
    const pad = short * 0.08;
    const avail = Math.max(1, boxW - pad * 2);
    const fitWidth = (text: string, cap: number) =>
      Math.min(cap, (avail / Math.max(4, text.length)) * 1.45);
    return (
      <div
        style={{
          ...style,
          background: layer.bg ?? "#fef3c7",
          borderRadius: layer.flat ? 0 : 24,
          boxShadow: layer.flat ? "none" : (style.boxShadow ?? "0 10px 40px rgba(0,0,0,0.35)"),
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: short * 0.06,
          padding: pad,
          textAlign: "center",
          fontFamily: "Inter, Helvetica, sans-serif",
          color: layer.fg ?? "#92400e",
        }}
      >
        {layer.lines?.length ? (
          layer.lines.map((line, i) => (
            <div
              key={i}
              style={{
                fontSize: fitWidth(line, boxH * 0.19),
                fontWeight: 800,
                lineHeight: 1.15,
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {line}
            </div>
          ))
        ) : (
          <>
            {layer.heading ? (
              <div
                style={{
                  fontSize: layer.fontSize ?? fitWidth(layer.heading, boxH * 0.3),
                  fontWeight: 900,
                  lineHeight: 1.05,
                  ...(layer.tracking
                    ? { letterSpacing: `${layer.tracking}em`, marginRight: `-${layer.tracking}em` }
                    : {}),
                }}
              >
                {layer.heading}
              </div>
            ) : null}
            {layer.subtext ? (
              // Subtext wraps, so width alone can't bound it: a long string at
              // the width-derived size grows enough lines to run off the card
              // (and under the caption band). Also solve for the size whose
              // wrapped block fits the vertical room left after the heading.
              (<div
                style={{
                  fontSize: Math.min(
                    boxH * 0.11,
                    boxW * 0.075,
                    Math.sqrt((boxH * 0.34 * avail) / (Math.max(12, layer.subtext.length) * 0.7)),
                  ),
                  fontWeight: 600,
                  opacity: 0.9,
                }}
              >
                {layer.subtext}
              </div>)
            ) : null}
            {layer.footnote ? (
              // Deliberately quiet and set apart — a URL should be findable,
              // not competing with the tagline for the same line.
              (<div
                style={{
                  marginTop: short * 0.05,
                  fontSize: Math.min(boxH * 0.055, boxW * 0.038),
                  fontWeight: 500,
                  letterSpacing: "0.06em",
                  opacity: 0.62,
                }}
              >
                {layer.footnote}
              </div>)
            ) : null}
          </>
        )}
      </div>
    );
  }
  if (layer.type === "placeholder") {
    return (
      <div
        style={{
          ...style,
          background: layer.color ?? "#3b5b7a",
          border: "4px dashed rgba(255,255,255,0.6)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ color: "white", fontSize: 64, fontFamily: "sans-serif", fontWeight: 700, opacity: 0.9 }}>
          {layer.label ?? layer.id}
        </span>
      </div>
    );
  }
  const media: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: layer.fit ?? "cover",
  };
  if (layer.ken) {
    // Ease the drift. A linear ramp holds constant velocity for the whole
    // scene, which reads as a mechanical slider rather than a camera move —
    // showwatcher's motion detector flags exactly that (easing score 0.04).
    const raw = Math.min(1, Math.max(0, t / Math.max(0.001, sceneSeconds)));
    const p = interpolate(raw, [0, 1], [0, 1], {
      easing: Easing.inOut(Easing.cubic),
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    const amt = layer.ken.amount ?? 0.12;
    const zoomScale = layer.ken.zoom === "out" ? 1 + amt * (1 - p) : 1 + amt * p;
    // Panning needs headroom: without it, a translate at scale 1.0 would slide
    // the image off its own box and show background.
    const reserve = layer.ken.pan ? amt : 0;
    const scale = zoomScale + reserve;
    // A translate inside scale() moves by scale × percent, while the hidden
    // overflow per side is only (scale-1)/2 — so a fixed reserve/2 shift
    // outgrows its margin exactly when zoom:"out" returns the scale to 1,
    // exposing a sliver of background at the frame edge (verified: black
    // right-edge pixels on the final frame). Derive the shift from the
    // headroom actually available at this instant instead, keeping a little
    // back to avoid subpixel seams.
    const shift = scale > 1 ? ((scale - 1) / (2 * scale)) * 100 * 0.92 * p : 0;
    const tx = layer.ken.pan === "left" ? -shift : layer.ken.pan === "right" ? shift : 0;
    const ty = layer.ken.pan === "up" ? -shift : layer.ken.pan === "down" ? shift : 0;
    media.transform = `scale(${scale.toFixed(4)}) translate(${tx.toFixed(3)}%, ${ty.toFixed(3)}%)`;
    media.transformOrigin = "center";
  }
  const video = <OffthreadVideo src={staticFile(layer.src!)} style={media} muted={layer.muted ?? true} />;
  // A clip shorter than its scene would otherwise freeze on its last frame
  // (OffthreadVideo has no `loop` prop — passing one is silently ignored).
  // Generated footage is capped at 6s while narration-driven scenes often run
  // longer, so this is the common case, not the exotic one.
  const shouldLoop =
    layer.loop !== false &&
    !!layer.srcDurationInFrames &&
    layer.srcDurationInFrames < sceneSeconds * fps - 1;
  return (
    <div style={style}>
      {layer.type === "image" ? (
        <Img src={staticFile(layer.src!)} style={media} />
      ) : shouldLoop ? (
        <Loop durationInFrames={layer.srcDurationInFrames!}>{video}</Loop>
      ) : (
        video
      )}
    </div>
  );
};

const OverlayView: React.FC<{ overlay: Overlay; sceneSeconds: number }> = ({ overlay, sceneSeconds }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const t = frame / fps;
  // Pop in over 0.35s, hold, fade out over the scene's last 0.3s.
  const appear = interpolate(t, [0.15, 0.5], [0, 1], {
    easing: Easing.out(Easing.back(1.6)),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fade = interpolate(t, [sceneSeconds - 0.3, sceneSeconds], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // "bottom" has to clear the caption band, which starts at height * 0.88 —
  // at 0.78 a stat pill overlapped the karaoke line on a 16:9 frame.
  const top = overlay.position === "bottom" ? height * 0.70 : overlay.position === "center" ? height * 0.42 : height * 0.09;
  const isStat = overlay.type === "stat";
  return (
    <div style={{ position: "absolute", top, width: "100%", textAlign: "center", opacity: fade }}>
      <div
        style={{
          display: "inline-block",
          transform: `scale(${appear})`,
          background: isStat ? "rgba(250,204,21,0.95)" : "rgba(0,0,0,0.65)",
          color: isStat ? "#1c1917" : "#ffffff",
          fontFamily: "Inter, sans-serif",
          fontWeight: 900,
          fontSize: (overlay.type === "title" ? 88 : isStat ? 76 : 52) * (overlay.scale ?? 1),
          letterSpacing: "0.02em",
          padding: isStat ? "18px 44px" : "12px 32px",
          borderRadius: 24,
          boxShadow: "0 8px 32px rgba(0,0,0,0.45)",
        }}
      >
        {overlay.text}
      </div>
    </div>
  );
};

const Captions: React.FC<{ words: CaptionWord[]; style?: VideoProps["captionStyle"] }> = ({ words, style }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const ms = (frame / fps) * 1000;
  // Show a rolling window of up to 4 words around the current one.
  const idx = words.findIndex((w) => ms >= w.startMs && ms < w.endMs);
  if (idx === -1) return null;
  const per = style?.wordsPerPage ?? 4;
  const start = Math.floor(idx / per) * per;
  const page = words.slice(start, start + per);
  return (
    <div
      style={{
        position: "absolute",
        bottom: height * (style?.bottom ?? 0.12),
        width: "88%",
        left: "6%",
        textAlign: "center",
        fontFamily: style?.fontFamily ?? "Inter, sans-serif",
        fontSize: style?.fontSize ?? 56,
        fontWeight: 800,
        textShadow: "0 2px 12px rgba(0,0,0,0.8)",
        textTransform: style?.uppercase ? "uppercase" : undefined,
        lineHeight: 1.2,
      }}
    >
      {page.map((w, i) => {
        const gi = start + i;              // global word index — keeps the palette
        const active = gi === idx;         // walking forward across the page break
        const pal = style?.palette;
        const colour = active
          ? style?.highlight ?? (pal ? pal[gi % pal.length] : "#facc15")
          : pal
            ? pal[gi % pal.length]
            : style?.color ?? "#ffffff";
        const wig = style?.wiggle ?? 0;
        const pop = active ? style?.bounce ?? 1 : 1;
        // Words are separated by margin alone — there is no whitespace text
        // node between these spans — and neither of the two things that make a
        // word bigger reserves any of it. `transform: scale()` is painted, not
        // laid out, and -webkit-text-stroke paints outside the glyph's metrics.
        // So a bouncing, stroked word grows into the gap and collides with its
        // neighbour: "watching physics," renders as "watchingphysics,".
        //
        // The room is reserved here instead. Two terms, each covering one
        // cause, and both are per word rather than a flat constant — a scaled
        // word overflows by half its OWN width times (bounce - 1), so a long
        // word overflows far more than a short one. A constant sized for
        // "watching" still overlaps on "extraordinarily".
        //
        // CHAR_EM is the width of an average character, measured rather than
        // guessed: sampled across this weight and family it runs 0.28em ("lll")
        // to 0.83em ("MMM"), mean 0.50. The high end is what matters, because
        // underestimating is what produces the bug, and uppercase is a
        // supported caption option. 0.7 clears every case tried, including
        // all-caps at bounce 1.4; 0.5 does not.
        //
        // Both terms vanish at bounce 1 with no stroke, so captions that use
        // neither are spaced exactly as before.
        const CHAR_EM = 0.7;
        const fontSizePx = style?.fontSize ?? 56;
        const strokePx = style?.stroke ? style?.strokeWidth ?? 6 : 0;
        const bounceMax = style?.bounce ?? 1;
        const halfBase = (style?.wordGap ?? 0.18) / 2;   // both sides sum to wordGap
        const gapEm =
          halfBase +
          strokePx / fontSizePx +
          (Math.max(0, bounceMax - 1) * (w.text.length * CHAR_EM)) / 2;
        return (
          <span
            key={`${gi}`}
            style={{
              color: colour,
              margin: `0 ${gapEm}em`,
              display: "inline-block",
              // rotate/scale need inline-block to apply to the word box
              transform: `rotate(${wig ? (gi % 2 ? wig : -wig) : 0}deg) scale(${pop})`,
              WebkitTextStroke: style?.stroke
                ? `${style?.strokeWidth ?? 6}px ${style.stroke}`
                : undefined,
              paintOrder: "stroke fill",   // outline behind the glyph, not over it
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};

/** Flat level, or a per-frame lookup when duck_music has written an envelope.
 *
 * Clamped at the last entry rather than falling off the end: the envelope is
 * built from the props' own scene durations, but a re-run of build_props can
 * lengthen the composition without duck_music being run again, and an
 * undefined volume silences the bed for the remainder instead of erroring. */
const musicVolume = (music: NonNullable<VideoProps["music"]>) => {
  const env = music.envelope;
  if (!env || env.length === 0) return music.volume ?? 0.25;
  return (frame: number) => env[Math.min(frame, env.length - 1)];
};

export const VideoComposition: React.FC<VideoProps> = (props) => {
  const { fps } = useVideoConfig();
  let from = 0;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {props.music ? (
        <Audio
          src={staticFile(props.music.src)}
          volume={musicVolume(props.music)}
        />
      ) : null}
      {props.scenes.map((scene) => {
        const seq = (
          <Sequence
            key={scene.id}
            from={from}
            durationInFrames={scene.durationInFrames}
            name={scene.id}
          >
            {scene.layers.map((layer) => (
              <LayerView key={layer.id} layer={layer} sceneSeconds={scene.durationInFrames / fps} />
            ))}
            {scene.audio ? <Audio src={staticFile(scene.audio)} /> : null}
            {scene.captions?.length ? <Captions words={scene.captions} style={{ ...props.captionStyle, ...scene.captionStyle }} /> : null}
            {scene.overlays?.map((o, i) => (
              <OverlayView key={i} overlay={o} sceneSeconds={scene.durationInFrames / fps} />
            ))}
          </Sequence>
        );
        from += scene.durationInFrames;
        return seq;
      })}
    </AbsoluteFill>
  );
};
