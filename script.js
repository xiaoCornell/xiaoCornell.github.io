document.querySelectorAll("[data-year]").forEach((node) => {
  node.textContent = new Date().getFullYear();
});

const page = document.body.dataset.page;
document.querySelectorAll("[data-nav]").forEach((link) => {
  if (link.dataset.nav === page) {
    link.classList.add("is-active");
  }
});

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  },
  {
    threshold: 0.16,
    rootMargin: "0px 0px -32px 0px",
  },
);

document.querySelectorAll(".reveal").forEach((node) => {
  observer.observe(node);
});

function normalizeVenueText(venue) {
  return String(venue ?? "")
    .replace(/Phys\.Rev\.Lett\./g, "Phys. Rev. Lett.")
    .replace(/Phys\.Rev\.B/g, "Phys. Rev. B")
    .replace(/Phys\.Rev\.A/g, "Phys. Rev. A")
    .replace(/Phys\.Rev\.Research/g, "Phys. Rev. Research")
    .replace(/Phys\.Rev\./g, "Phys. Rev. ")
    .replace(/Sci\.Bull\./g, "Sci. Bull.")
    .replace(/Acta Phys\.Sin\./g, "Acta Phys. Sin.")
    .replace(/J\.Phys\.A/g, "J. Phys. A")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function formatPublicationVenue(venue) {
  return normalizeVenueText(venue).replace(/\s+\d.*$/, "").trim();
}

function formatPublicationYear(publication) {
  const venueYear = publication.venue.match(/\((\d{4})\)\s*$/);
  return venueYear ? venueYear[1] : publication.year;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatPublicationTitle(title) {
  return String(title ?? "")
    .replace(/\$([^$]+)\$/g, "$1")
    .replace(/\\mathcal\{([^}]+)\}/g, "$1")
    .replace(/\\mathrm\{([^}]+)\}/g, "$1")
    .replace(/\\text\{([^}]+)\}/g, "$1")
    .replace(/_\{([^}]+)\}/g, "$1")
    .replace(/\^\{([^}]+)\}/g, "$1")
    .replace(/_([A-Za-z0-9])/g, "$1")
    .replace(/\^([A-Za-z0-9])/g, "$1")
    .replace(/\\_/g, "_")
    .replace(/[{}]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function buildPublicationSummary(publication) {
  const venue = normalizeVenueText(publication.venue);
  if (publication.peer_reviewed) {
    return `Published in ${venue}.`;
  }
  return `Preprint: ${venue}.`;
}

function renderPublicationLinks(publication) {
  return (publication.links || [])
    .filter((link) => link.label === "DOI" || link.label === "arXiv")
    .slice(0, 2)
    .map((link) => `<a href="${escapeHtml(link.url)}">${escapeHtml(link.label)}</a>`)
    .join("");
}

function publicationSortKey(publication, index) {
  const parsedSortDate = Date.parse(publication.sort_date ?? "");
  return {
    sortDate: Number.isNaN(parsedSortDate) ? 0 : parsedSortDate,
    effectiveYear: Number.parseInt(formatPublicationYear(publication), 10) || 0,
    originalIndex: index,
  };
}

async function syncSelectedPublications() {
  const cards = document.querySelectorAll("[data-selected-publication]");
  const publicationCountNode = document.querySelector("[data-publication-count]");
  const peerReviewedCountNode = document.querySelector("[data-peer-reviewed-count]");

  if (!cards.length && !publicationCountNode && !peerReviewedCountNode) {
    return;
  }

  try {
    const response = await fetch("data/publications.json", { cache: "no-store" });
    if (!response.ok) {
      return;
    }

    const payload = await response.json();
    if (publicationCountNode) {
      publicationCountNode.textContent = String(payload.publication_count ?? "");
    }
    if (peerReviewedCountNode) {
      peerReviewedCountNode.textContent = String(payload.peer_reviewed_count ?? "");
    }

    const publications = [...(payload.publications || [])]
      .map((publication, index) => ({
        ...publication,
        _sort: publicationSortKey(publication, index),
      }))
      .sort((left, right) => {
        if (left._sort.sortDate !== right._sort.sortDate) {
          return right._sort.sortDate - left._sort.sortDate;
        }
        if (left._sort.effectiveYear !== right._sort.effectiveYear) {
          return right._sort.effectiveYear - left._sort.effectiveYear;
        }
        return left._sort.originalIndex - right._sort.originalIndex;
      })
      .slice(0, cards.length);

    cards.forEach((card, index) => {
      const publication = publications[index];
      if (!publication) {
        return;
      }

      card.innerHTML = `
        <div class="pub-meta"><span>${escapeHtml(formatPublicationYear(publication))}</span><span>${escapeHtml(formatPublicationVenue(publication.venue))}</span></div>
        <h3>${escapeHtml(formatPublicationTitle(publication.title))}</h3>
        <p>${escapeHtml(buildPublicationSummary(publication))}</p>
        <div class="link-row">${renderPublicationLinks(publication)}</div>
      `;
    });
  } catch {
    // Keep the static fallback content when publication sync data cannot be loaded.
  }
}

void syncSelectedPublications();
