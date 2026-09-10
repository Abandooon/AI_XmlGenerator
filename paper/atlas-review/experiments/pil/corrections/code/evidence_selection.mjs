/** Match an article or its subparagraph, never a longer article number. */
export function matchesProvision(provision, requested) {
  return provision === requested || provision.startsWith(`${requested}(`);
}
