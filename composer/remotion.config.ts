import { Config } from "@remotion/cli/config";

Config.setEntryPoint("src/index.ts");
Config.setVideoImageFormat("png");
// jpeg frames default the output to yuvj420p, which the quality check flags
// as a social-platform compatibility risk. Pin the standard range.
Config.setPixelFormat("yuv420p");
Config.setOverwriteOutput(true);
