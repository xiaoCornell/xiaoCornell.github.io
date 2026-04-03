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

function formatPublicationVenue(venue) {
  return venue
    .replace(/\s+\d.*$/, "")
    .replace(/Phys\.Rev\.Lett\./g, "Phys. Rev. Lett.")
    .replace(/Phys\.Rev\./g, "Phys. Rev. ")
    .replace(/Sci\.Bull\./g, "Sci. Bull.")
    .replace(/Acta Phys\.Sin\./g, "Acta Phys. Sin.")
    .replace(/J\.Phys\.A/g, "J. Phys. A")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function formatPublicationYear(publication) {
  const venueYear = publication.venue.match(/\((\d{4})\)\s*$/);
  return venueYear ? venueYear[1] : publication.year;
}

async function syncSelectedPublications() {
  const cards = document.querySelectorAll("[data-selected-publication]");
  if (!cards.length) {
    return;
  }

  try {
    const response = await fetch("data/publications.json", { cache: "no-store" });
    if (!response.ok) {
      return;
    }

    const payload = await response.json();
    const publications = new Map(
      (payload.publications || []).map((publication) => [publication.recid, publication]),
    );

    cards.forEach((card) => {
      const publication = publications.get(card.dataset.selectedPublication);
      if (!publication) {
        return;
      }

      const yearNode = card.querySelector("[data-publication-year]");
      if (yearNode) {
        yearNode.textContent = formatPublicationYear(publication);
      }

      const venueNode = card.querySelector("[data-publication-venue]");
      if (venueNode) {
        venueNode.textContent = formatPublicationVenue(publication.venue);
      }

      const linksNode = card.querySelector("[data-publication-links]");
      if (linksNode) {
        linksNode.innerHTML = (publication.links || [])
          .filter((link) => link.label === "DOI" || link.label === "arXiv")
          .slice(0, 2)
          .map((link) => `<a href="${link.url}">${link.label}</a>`)
          .join("");
      }
    });
  } catch {
    // Keep the static fallback content when publication sync data cannot be loaded.
  }
}

void syncSelectedPublications();
