# Putting frontierfourpress.com on GitHub Pages

Do these steps only after you have approved the local preview.

Your DNS is hosted at **GoDaddy** (nameservers `ns53/ns54.domaincontrol.com`).
GoDaddy: My Products > frontierfourpress.com > **DNS** > DNS Records.

## What is there today (looked up November 22, 2026)

| Type | Name | Value | What to do |
|---|---|---|---|
| A | @ | 3.33.130.190 | **Delete** (GoDaddy parking page) |
| A | @ | 15.197.148.33 | **Delete** (GoDaddy parking page) |
| CNAME | www | @ (frontierfourpress.com) | **Edit** value to `oladehin.github.io` |
| MX | @ | aspmx.l.google.com and alt1 to alt4 | Leave untouched |
| TXT | @ | v=spf1 include:dc-aa8e722993._spfm.frontierfourpress.com ~all | Leave untouched |
| TXT | @ | google-site-verification=Uxhg8a... | Leave untouched |
| TXT | google._domainkey | v=DKIM1; k=rsa; p=... | Leave untouched |
| TXT | _dmarc | v=DMARC1; p=quarantine; ... | Leave untouched |

GoDaddy may also show NS, SOA and `_domainconnect` rows, and maybe a `dc-aa8e722993._spfm` TXT
row that feeds the SPF record above. **Leave every one of those alone.**

The rule: **you only touch A and AAAA records on `@` and the CNAME on `www`.** Nothing of type
MX or TXT is edited or deleted. Mail keeps flowing the whole time.

## Step 1. Verify the domain with GitHub (prevents domain takeover)

1. GitHub > your profile picture > Settings > **Pages** > Add a domain > `frontierfourpress.com`.
2. GitHub shows a TXT record. Add it in GoDaddy as a **new** record:

| Type | Name | Value | TTL |
|---|---|---|---|
| TXT | `_github-pages-challenge-oladehin` | (the code GitHub shows you) | 1 hour |

This is a new name, so it does not touch your existing `@` TXT records.
3. Back in GitHub, click **Verify**. It can take a few minutes.

## Step 2. Publish the repository

1. Create a repository (for example `frontierfourpress-website`) under the `oladehin` account and push this folder.
2. Repository > Settings > **Pages**:
   - Source: **Deploy from a branch**
   - Branch: `main`, folder **`/docs`**
   - Custom domain: `frontierfourpress.com` (the `docs/CNAME` file already says this) > Save.

## Step 3. Point the domain at GitHub (at GoDaddy)

Delete the two parking A records on `@`, then add:

| Type | Name | Value | TTL |
|---|---|---|---|
| A | @ | 185.199.108.153 | 1 hour |
| A | @ | 185.199.109.153 | 1 hour |
| A | @ | 185.199.110.153 | 1 hour |
| A | @ | 185.199.111.153 | 1 hour |
| AAAA | @ | 2606:50c0:8000::153 | 1 hour |
| AAAA | @ | 2606:50c0:8001::153 | 1 hour |
| AAAA | @ | 2606:50c0:8002::153 | 1 hour |
| AAAA | @ | 2606:50c0:8003::153 | 1 hour |

Edit the existing `www` CNAME:

| Type | Name | Value | TTL |
|---|---|---|---|
| CNAME | www | oladehin.github.io | 1 hour |

If GoDaddy has **Forwarding** turned on for the domain (Domain settings > Forwarding),
turn it off; it re-creates the parking A records.

No CAA records exist today, so nothing is needed there. If you add CAA records later, include
`0 issue "letsencrypt.org"` or GitHub cannot issue the HTTPS certificate.

## Step 4. HTTPS

After DNS updates (usually under an hour, up to 24), GitHub Pages issues a certificate.
Repository > Settings > Pages > tick **Enforce HTTPS** once it is offered.
`www.frontierfourpress.com` then redirects to `frontierfourpress.com` automatically.

## Check it worked (run on your Mac)

```bash
dig +short frontierfourpress.com A
```

Expect the four 185.199.x.153 addresses.

```bash
dig +short www.frontierfourpress.com CNAME
```

Expect `oladehin.github.io.`

```bash
dig +short frontierfourpress.com MX
```

Expect the same five Google servers as before. If this list changes, something went wrong:
stop and restore the MX rows from the table above.
