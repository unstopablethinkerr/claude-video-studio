# projects/

Each video is one folder here. `starter/` is a ready-to-edit blank project.

Create a new one (non-interactive, safe for Claude Code):

    cd projects && npx --yes hyperframes@0.9.19 init my-video --non-interactive --example blank --skip-skills

Then ask Claude Code to edit `projects/my-video/index.html`, and render with:

    npx --yes hyperframes@0.9.19 render projects/my-video -o outputs/my-video.mp4
