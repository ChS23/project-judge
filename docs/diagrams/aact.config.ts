// import { defineConfig } from "aact";
// TODO: defineConfig fails with jiti on Node 20 (ERR_PACKAGE_PATH_NOT_EXPORTED)
// Works on Node 22+ or with npx (not pnpx). Track: https://github.com/ChS23/aact

export default {
  source: {
    type: "plantuml",
    path: "./c4-container.puml",
  },

  rules: {
    // Enabled: relevant for our architecture
    acyclic: true,            // No circular dependencies
    cohesion: true,           // Boundaries: more internal than external connections
    stableDependencies: true, // Dependencies point toward stable modules
    commonReuse: true,        // Common Reuse Principle

    // Disabled: not applicable for this PoC
    acl: false,           // People (student/instructor) are external actors, not containers
    crud: false,          // Redis is a task queue broker, not a database
    dbPerService: false,  // Redis is intentionally shared between app and worker
    apiGateway: false,    // No API gateway in PoC
  },
};
