---
name: Code Quality Styling UX Recommendations
overview: Recommendations for code quality (remove debug logs, standardize error handling), styling (use design tokens consistently, unify patterns), and UX (modals, loading, destructive actions, mobile nav, feedback).
todos:
  - id: todo-1770164997974-9nrtf6be9
    content: ""
    status: pending
isProject: false
---

# Recommendations: Code Quality, Styling, and UX

Recommendations are grouped by area. Each item is scoped so you can adopt them incrementally.

---

## 1. Code quality

### 1.1 Remove or gate debug logging

**Current:** [dashboard/page.tsx](frontend/app/dashboard/page.tsx), [EditItemModal.tsx](frontend/components/EditItemModal.tsx), and [dashboard/groups/[id]/page.tsx](frontend/app/dashboard/groups/[id]/page.tsx) use `console.log` / `console.error` for loading and save flows.

**Recommendation:** Remove `console.log` calls (e.g. "Dashboard loaded wishlist items", "EditItemModal opened", "Saving item", "Dashboard: Setting editing item"). Keep or gate `console.error` in catch blocks (e.g. only in development via `process.env.NODE_ENV === 'development'`) so production logs stay clean.

### 1.2 Replace `alert()` with inline error UI

**Current:** Several components use `alert()` for errors: [EditItemModal.tsx](frontend/components/EditItemModal.tsx) (update/delete), [ImageUpload.tsx](frontend/components/ImageUpload.tsx), [PurchaseButton.tsx](frontend/components/PurchaseButton.tsx), [DeleteItemButton.tsx](frontend/components/DeleteItemButton.tsx), [RemoveMemberButton.tsx](frontend/components/RemoveMemberButton.tsx), [manage/page.tsx](frontend/app/dashboard/groups/[id]/manage/page.tsx), [wishlists/new/page.tsx](frontend/app/dashboard/wishlists/new/page.tsx).

**Recommendation:** Use inline error state and a small message area (like login/register and [invite/[token]/page.tsx](frontend/app/invite/[token]/page.tsx)) or a shared toast/snackbar so errors are in-context and consistent. Reduces reliance on native `alert()` and improves accessibility.

### 1.3 Optional: shared error / toast feedback

Introduce a small toast or snackbar (e.g. React state + context, or a minimal library) for success/error after actions (e.g. "Item updated", "Failed to claim"). Reuse it from modals and buttons that currently use `alert()` or have no success feedback (e.g. [DraggableWishlist.tsx](frontend/components/DraggableWishlist.tsx) reorder succeeds with no message).

---

## 2. Styling

### 2.1 Use design tokens from `globals.css` consistently

**Current:** [globals.css](frontend/app/globals.css) defines CSS variables (`--primary`, `--background`, `--muted`, `--destructive`, etc.) and [tailwind.config.ts](frontend/tailwind.config.ts) maps them to Tailwind utilities (`bg-primary`, `text-muted-foreground`, etc.). Most components still use raw Tailwind colors (`bg-blue-600`, `text-gray-600`, `bg-white dark:bg-gray-800`).

**Recommendation:** Prefer token-based classes so theming and dark mode stay consistent and future theme changes are easier:

- Primary actions: `bg-primary text-primary-foreground hover:opacity-90` instead of `bg-blue-600 text-white hover:bg-blue-700`.
- Surfaces: `bg-card text-card-foreground` or `bg-background` where appropriate instead of `bg-white dark:bg-gray-800`.
- Muted text: `text-muted-foreground` instead of `text-gray-600 dark:text-gray-300`.
- Destructive: `bg-destructive text-destructive-foreground` for delete/remove buttons.

Apply incrementally (e.g. start with [DashboardNav](frontend/components/DashboardNav.tsx), primary buttons, then cards and text).

### 2.2 Unify border radius and form input styles

**Current:** Mix of `rounded-md` (login, register, groups/new) and `rounded-lg` (dashboard cards, modals, wishlists/new). Input classes are repeated across forms.

**Recommendation:** Standardize on one radius scale (e.g. `rounded-lg` for cards/modals, `rounded-md` for inputs/buttons, or use `rounded-md` / `rounded-lg` from `tailwind.config`). Extract a shared input class (e.g. in `globals.css` as `@layer components` or a small `Input` component) and reuse it in login, register, EditItemModal, wishlists/new, and groups/new to reduce duplication and drift.

### 2.3 Optional: shared Button and Card components

Add minimal `Button` (primary, secondary, destructive, disabled state) and `Card` wrappers that use the design tokens. Use them across dashboard, auth, and modals for consistent look and fewer one-off class strings.

---

## 3. User experience

### 3.1 Modal accessibility and behavior

**Current:** [ItemDetailModal.tsx](frontend/components/ItemDetailModal.tsx), [EditItemModal.tsx](frontend/components/EditItemModal.tsx), and [InviteMemberModal.tsx](frontend/components/InviteMemberModal.tsx) close only via backdrop click or explicit close button. No Escape key, no focus trap, close button has no `aria-label`.

**Recommendation:**

- Close on Escape: add `useEffect` with `keydown` listener for `Escape` calling `onClose` when modal is open.
- Focus trap: when open, focus the first focusable element (e.g. close button or first input) and trap Tab inside the modal; on close, return focus to the trigger element if possible.
- Add `aria-label="Close"` (or similar) to the close (X) buttons so screen readers have a clear label.

### 3.2 Loading states

**Current:** Dashboard uses skeleton placeholders (`animate-pulse`) for groups and wishlist sections, but other pages (wishlists page, groups page, manage page, auth) use plain "Loading..." text.

**Recommendation:** Use skeleton loaders for list/card content (e.g. wishlists list, groups list, group detail) so layout shift is reduced and perceived performance is consistent with the main dashboard. Keep simple "Loading..." only for full-page or minimal content where skeletons do not add value.

### 3.3 Destructive actions: in-app confirmation

**Current:** Delete item, delete group, remove member, and revoke invitation use `confirm()` for confirmation. It works but is native and not styled.

**Recommendation:** Add a small reusable confirmation modal (e.g. "Are you sure? This cannot be undone." with Cancel / Delete buttons). Use it from EditItemModal (delete item), DeleteItemButton, manage page (delete group), RemoveMemberButton, and AddMemberForm (revoke invite). Styling can match the app (e.g. destructive button using `bg-destructive`) and improves consistency and accessibility (focus, Escape, aria).

### 3.4 Mobile navigation

**Current:** [DashboardNav.tsx](frontend/components/DashboardNav.tsx) is a horizontal bar: logo, Groups link, Wishlist link, "Hello, {userName}", ThemeToggle, Sign Out. On small screens this can wrap or overflow.

**Recommendation:** Add a mobile-friendly nav: e.g. hamburger menu below a breakpoint (e.g. `md`) that toggles a drawer or dropdown with the same links and actions. Keep the current layout for larger screens. Ensures all actions are reachable on small screens without horizontal scroll.

### 3.5 Success feedback for reorder

**Current:** [DraggableWishlist.tsx](frontend/components/DraggableWishlist.tsx) calls `onReorder()` after a successful reorder but shows no explicit success message; errors are only in console.

**Recommendation:** After a successful reorder, show a short-lived success message (inline or via the optional toast from 1.3), e.g. "Order saved." On error, show an inline or toast error instead of only logging. Improves confidence that the action worked.

### 3.6 Optional: initial auth loading

**Current:** [AuthContext](frontend/lib/contexts/AuthContext.tsx) sets `isLoading` while restoring session; pages that depend on auth often render nothing or redirect. A brief flash can occur.

**Recommendation:** Show a single global loading UI (e.g. minimal spinner or skeleton) while `isLoading` is true and the user is on a protected route, so the transition from "checking auth" to "dashboard" or "login" feels intentional rather than blank.

---

## 4. Suggested order of work


| Priority    | Area         | Items                                                                              |
| ----------- | ------------ | ---------------------------------------------------------------------------------- |
| Quick wins  | Code quality | 1.1 Remove console.log; 1.2 Replace alert with inline error in 1–2 key flows       |
| Consistency | Styling      | 2.1 Use design tokens in nav and primary buttons; 2.2 Unify radius and input class |
| UX          | Modals       | 3.1 Escape + focus trap + aria-label for modals                                    |
| UX          | Loading      | 3.2 Skeleton loading on wishlists/groups list pages                                |
| UX          | Destructive  | 3.3 Confirmation modal for delete/remove/revoke                                    |
| UX          | Mobile       | 3.4 Hamburger nav on small screens                                                 |
| Polish      | Feedback     | 1.3 Toast option; 3.5 Reorder success message; 3.6 Auth loading UI                 |


You can implement in phases: e.g. Phase 1 = 1.1, 1.2, 2.1, 3.1; Phase 2 = 2.2, 3.2, 3.3; Phase 3 = 3.4, 3.5, and optional toast/auth loading.