# Confluence Setup for Development

## Important Note

**Confluence is NOT open-source** - it's a proprietary Atlassian product. There are no public "open-source Confluence instances" available for API access.

## Best Options for Development/Testing

### Option 1: Free Atlassian Cloud Trial (Recommended) ⭐

**This is the easiest option:**

1. **Sign up for a free trial:**
   - Go to https://www.atlassian.com/try/cloud/signup
   - Create a free account (no credit card required for trial)
   - You'll get a free Confluence instance for 7 days (can be extended)

2. **Your Confluence URL will look like:**
   ```
   https://your-site-name.atlassian.net/wiki
   ```
   Replace `your-site-name` with the site name you chose during signup.

3. **Create an API Token:**
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Copy the token

4. **Your .env file should look like:**
   ```env
   CONFLUENCE_URL=https://your-site-name.atlassian.net/wiki
   CONFLUENCE_USERNAME=your-email@example.com
   CONFLUENCE_API_TOKEN=your-api-token-here
   GOOGLE_API_KEY=your-google-api-key
   ```

5. **Create some test pages:**
   - Create a space (e.g., "TEST")
   - Add a few pages with sample documentation
   - Use this space key when indexing

**Advantages:**
- Free for 7 days (can extend)
- Full API access
- Real Confluence environment
- No restrictions

---

### Option 2: Use Your Existing Confluence

If you already have access to a Confluence instance (work, personal, etc.), you can use it:

```env
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-api-token
GOOGLE_API_KEY=your-google-api-key
```

**Note:** Make sure you have permission to use the API and create test spaces.

---

### Option 3: Mock Data for Testing (Advanced)

If you want to test the RAG pipeline without Confluence access, you can modify the fetcher to use sample data. However, this requires code changes and won't test the Confluence integration.

---

## Why No Public Open-Source Option?

1. **Confluence is proprietary** - Atlassian doesn't offer a public/open-source version
2. **API Access Requires Authentication** - Even public documentation sites typically don't allow API access
3. **Security/Privacy** - Organizations don't expose their Confluence APIs publicly

## Recommended Approach

**For development/testing, use the free Atlassian Cloud trial (Option 1).** It's:
- ✅ Free (7 days, extendable)
- ✅ Full-featured
- ✅ Perfect for testing
- ✅ No setup complexity
- ✅ Real Confluence environment

## Getting Started with Free Trial

1. Sign up: https://www.atlassian.com/try/cloud/signup
2. Create a test space and add some pages
3. Get your API token
4. Configure your `.env` file
5. Start indexing!

## Example .env Configuration

```env
# Confluence Configuration (Free Trial Example)
CONFLUENCE_URL=https://my-test-site.atlassian.net/wiki
CONFLUENCE_USERNAME=your.email@gmail.com
CONFLUENCE_API_TOKEN=ATATT3xFfGF0...
GOOGLE_API_KEY=AIzaSy...
```

Replace the values with your actual credentials from the trial account.

