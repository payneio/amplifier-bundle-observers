"""Observer loading from bundle paths.

This module handles loading observer definitions from markdown files with YAML frontmatter,
similar to how agents are loaded in Amplifier.

Observer references support:
- @bundle:path/to/observer - Resolved via mention_resolver capability
- path/to/observer - Relative to base_path
- ./local/observer.md - Local file path
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class MentionResolver(Protocol):
    """Protocol for mention resolution (matches BaseMentionResolver)."""

    def resolve(self, mention: str) -> Path | None:
        """Resolve an @-mention to a file path."""
        ...


@dataclass
class ContextFile:
    """A resolved context file from an @-mention."""

    path: str
    content: str
    source_mention: str


@dataclass
class LoadedObserver:
    """A fully loaded observer definition with resolved @-mentions."""

    name: str
    description: str
    model: str
    timeout: int
    tools: list[str]
    instruction: str  # Markdown body (raw, @-mentions not yet resolved)
    context_files: list[ContextFile] = field(default_factory=list)

    def get_full_instruction(self) -> str:
        """Get instruction with resolved context files appended."""
        if not self.context_files:
            return self.instruction

        context_parts = []
        for cf in self.context_files:
            context_parts.append(f'<context_file path="{cf.path}">\n{cf.content}\n</context_file>')

        context_block = "\n\n".join(context_parts)
        return f"{self.instruction}\n\n---\n\n{context_block}"


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown text.

    Args:
        text: Markdown text with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter_dict, body_text)
    """
    import re

    import yaml

    pattern = r"^---\s*\n(.*?)\n---\s*\n?"
    match = re.match(pattern, text, re.DOTALL)

    if not match:
        return {}, text

    yaml_content = match.group(1)
    body = text[match.end() :]

    try:
        frontmatter = yaml.safe_load(yaml_content) or {}
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse frontmatter YAML: {e}")
        frontmatter = {}

    return frontmatter, body


def parse_mentions(text: str) -> list[str]:
    """Extract @-mentions from text, excluding code blocks.

    Args:
        text: Text to parse for @-mentions

    Returns:
        List of mention strings (e.g., ["@bundle:path/file.md", "@local/file.md"])
    """
    import re

    # Remove code blocks first
    code_block_pattern = r"```[\s\S]*?```|`[^`]+`"
    text_without_code = re.sub(code_block_pattern, "", text)

    # Find @-mentions (word chars, colons, slashes, dots, hyphens)
    mention_pattern = r"@[\w:/.@-]+"
    mentions = re.findall(mention_pattern, text_without_code)

    return mentions


async def resolve_mentions(
    text: str,
    mention_resolver: MentionResolver | None,
    base_path: Path,
) -> list[ContextFile]:
    """Resolve @-mentions in text to their content.

    Args:
        text: Text containing @-mentions
        mention_resolver: Resolver for @bundle:path mentions (from coordinator capability)
        base_path: Base path for relative file resolution (fallback)

    Returns:
        List of resolved ContextFile objects
    """
    mentions = parse_mentions(text)
    context_files = []
    seen_paths: set[str] = set()

    for mention in mentions:
        try:
            path = resolve_mention_path(mention, mention_resolver, base_path)
            if path and str(path) not in seen_paths and path.exists():
                seen_paths.add(str(path))
                content = path.read_text(encoding="utf-8")
                context_files.append(
                    ContextFile(
                        path=str(path),
                        content=content,
                        source_mention=mention,
                    )
                )
        except Exception as e:
            logger.debug(f"Could not resolve mention {mention}: {e}")

    return context_files


def resolve_mention_path(
    mention: str,
    mention_resolver: MentionResolver | None,
    base_path: Path,
) -> Path | None:
    """Resolve a mention to a file path.

    Resolution order:
    1. If starts with @, use mention_resolver (bundle resolution)
    2. Otherwise, resolve relative to base_path

    Args:
        mention: Mention string (with or without @ prefix)
        mention_resolver: Resolver for @bundle:path mentions
        base_path: Base path for relative references

    Returns:
        Resolved Path or None if not resolvable
    """
    # If it's an @-mention, use the resolver
    if mention.startswith("@"):
        if mention_resolver:
            resolved = mention_resolver.resolve(mention)
            if resolved:
                return resolved
            logger.debug(f"mention_resolver could not resolve: {mention}")
        else:
            logger.debug(f"No mention_resolver available for: {mention}")
        return None

    # Relative reference - resolve against base_path
    ref = mention
    path = base_path / ref
    if path.exists():
        return path

    # Try with .md extension
    path_md = base_path / f"{ref}.md"
    if path_md.exists():
        return path_md

    return None


def _get_bundles_from_resolver(mention_resolver: MentionResolver | None) -> dict[str, Any]:
    """Extract bundles dict from various mention resolver implementations.

    Handles:
    - BaseMentionResolver: has .bundles directly
    - AppMentionResolver: wraps BaseMentionResolver via .foundation_resolver

    Args:
        mention_resolver: The mention resolver instance (may be wrapped)

    Returns:
        Dict mapping bundle names to bundle objects with base_path
    """
    if not mention_resolver:
        return {}

    # 1. Direct bundles attribute (BaseMentionResolver)
    bundles = getattr(mention_resolver, "bundles", None)
    if bundles:
        return bundles

    # 2. Via foundation_resolver (AppMentionResolver wraps BaseMentionResolver)
    foundation = getattr(mention_resolver, "foundation_resolver", None)
    if foundation:
        bundles = getattr(foundation, "bundles", None)
        if bundles:
            return bundles

    return {}


def resolve_observer_path(
    observer_ref: str,
    mention_resolver: MentionResolver | None,
    base_path: Path,
) -> Path:
    """Resolve observer reference to file path.

    Patterns:
    - "@bundle:observers/name" → resolved via mention_resolver
    - "observers/name" → tries base_path first, then registered bundle base_paths

    Args:
        observer_ref: Observer reference string
        mention_resolver: Resolver for @bundle:path mentions
        base_path: Base path for relative references (fallback)

    Returns:
        Resolved Path to observer file

    Raises:
        FileNotFoundError: If observer file cannot be found
    """
    # If it's an @-mention, use the resolver
    if observer_ref.startswith("@"):
        if mention_resolver:
            resolved = mention_resolver.resolve(observer_ref)
            if resolved and resolved.exists():
                return resolved
            # Try with .md extension
            ref_with_md = observer_ref if observer_ref.endswith(".md") else f"{observer_ref}.md"
            resolved_md = mention_resolver.resolve(ref_with_md)
            if resolved_md and resolved_md.exists():
                return resolved_md
            raise FileNotFoundError(f"Observer not found via mention_resolver: {observer_ref}")
        raise FileNotFoundError(f"No mention_resolver available to resolve: {observer_ref}")

    # Relative reference - try multiple sources
    tried_paths: list[Path] = []

    # 1. Try base_path first (original behavior)
    path = base_path / observer_ref
    tried_paths.append(path)
    if path.exists():
        return path

    path_md = base_path / f"{observer_ref}.md"
    tried_paths.append(path_md)
    if path_md.exists():
        return path_md

    # 2. Try bundle base_paths from mention_resolver
    # This handles cases where base_path is cwd() but the observer
    # lives in an included bundle's directory
    bundles: dict[str, Any] = _get_bundles_from_resolver(mention_resolver)
    if bundles:
        for bundle_name, bundle in bundles.items():
            bundle_base = getattr(bundle, "base_path", None)
            if bundle_base:
                bundle_path = bundle_base / observer_ref
                if bundle_path not in tried_paths:
                    tried_paths.append(bundle_path)
                    if bundle_path.exists():
                        logger.debug(f"Found observer in bundle '{bundle_name}': {bundle_path}")
                        return bundle_path

                bundle_path_md = bundle_base / f"{observer_ref}.md"
                if bundle_path_md not in tried_paths:
                    tried_paths.append(bundle_path_md)
                    if bundle_path_md.exists():
                        logger.debug(f"Found observer in bundle '{bundle_name}': {bundle_path_md}")
                        return bundle_path_md

    raise FileNotFoundError(
        f"Observer not found: {observer_ref} (tried {len(tried_paths)} locations: "
        f"{', '.join(str(p) for p in tried_paths[:4])}{'...' if len(tried_paths) > 4 else ''})"
    )


async def load_observer(
    observer_ref: str,
    mention_resolver: MentionResolver | None,
    base_path: Path,
) -> LoadedObserver:
    """Load an observer from a reference.

    Args:
        observer_ref: "@bundle:observers/name" or "observers/name" (relative)
        mention_resolver: Resolver for @bundle:path mentions (from coordinator capability)
        base_path: Base path for relative references

    Returns:
        LoadedObserver with resolved @-mentions

    Raises:
        FileNotFoundError: If observer file cannot be found
        ValueError: If observer file is malformed
    """
    # 1. Resolve observer path
    path = resolve_observer_path(observer_ref, mention_resolver, base_path)
    logger.debug(f"Loading observer from: {path}")

    # 2. Parse markdown + frontmatter
    content = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)

    # 3. Extract observer config from frontmatter
    obs_config = frontmatter.get("observer", {})
    if not obs_config:
        raise ValueError(f"Observer file missing 'observer:' section: {path}")

    tools = frontmatter.get("tools", [])

    # 4. Resolve @-mentions in the body
    context_files = await resolve_mentions(body, mention_resolver, path.parent)

    # 5. Build LoadedObserver
    return LoadedObserver(
        name=obs_config.get("name", path.stem),
        description=obs_config.get("description", ""),
        model=obs_config.get("model", "claude-3-5-haiku-latest"),
        timeout=obs_config.get("timeout", 30),
        tools=tools,
        instruction=body.strip(),
        context_files=context_files,
    )
