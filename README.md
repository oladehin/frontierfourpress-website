# frontierfourpress.com

One-page site for *Escape Velocity* (Frontier Four Press). Static HTML and CSS, no JavaScript,
no trackers, no third-party requests. Served by GitHub Pages from `docs/`.

## Change something

1. Edit `site.config.json` (on-sale date, pre-order link, endorsement, contact email, cover and logo paths, fonts).
2. Run:

```bash
python3 build.py
```

3. Preview `docs/index.html`, then commit `docs/` along with your change.

The build stops with an error if the page contains an em dash or a banned product or company
name. `Amazon` is allowed only on the pre-order button. To also check a name you do not want
written into this public repo:

```bash
FFP_EXTRA_BANNED="Name One,Name Two" python3 build.py
```

## Switches in site.config.json

| Key | Empty | Set |
|---|---|---|
| `preorder.url` | Shows "Pre-order opens December 1" (not a link) | Shows a "Pre-order on Amazon" button |
| `endorsement.quote` | Section hidden | Quote and attribution shown |
| `contactEmail` | Marked placeholders | Contact button and footer email |
| `cover.path` file | Marked placeholder cover | Real cover on page and in the share image |
| `logo.path` file | Type-set Stack placeholder | Designer logo in the footer |

Fonts: put the designer's family names in `fonts.display` and `fonts.sans`. If they are web
fonts you host yourself, add the `.woff2` files to `assets/source/fonts/` and list them:

```json
"files": [
  {"family": "Display Name", "path": "assets/source/fonts/display-regular.woff2", "style": "normal", "weight": "400"},
  {"family": "Display Name", "path": "assets/source/fonts/display-italic.woff2",  "style": "italic", "weight": "400"}
]
```

## Layout of this folder

- `site.config.json`: every value you will change
- `src/`: page template, CSS, images
- `tools/share-card.html`: template for the 1200 x 630 share image
- `build.py`: makes `docs/` and renders the share image and favicons with Chrome
- `docs/`: the built site GitHub Pages serves (do not hand-edit)
- `DNS_SETUP.md`: exact GoDaddy records, leaving Google Workspace mail untouched

## Image credit

Divider plate: Isaac Newton, cannonball diagram, *Principia*, American edition, 1846, p. 513.
Public domain (Wikimedia Commons, "Principia1846-513.png").
