---
# Leave the homepage title empty to use the site title
title: ''
date: 2024-01-01
type: landing

design:
  spacing:
    padding: ['0', '0', '0', '0']
    section_padding: ['py-8 md:py-16']

sections:
  # ── 1. BIOGRAPHY ──────────────────────────────────────────────────────────
  - block: about.biography
    id: about
    content:
      title: About
      username: admin

  # ── 2. KEY STATS ──────────────────────────────────────────────────────────
  - block: stats
    content:
      items:
        - statistic: "30+"
          description: |
            Peer-reviewed  
            publications
        - statistic: "700+"
          description: |
            Citations  
            (Google Scholar)
        - statistic: "14"
          description: |
            h-index  
            (Google Scholar)
    design:
      css_class: "bg-gray-100 dark:bg-gray-900"

  # ── 3. RESEARCH AREAS ─────────────────────────────────────────────────────
  - block: features
    id: research
    content:
      title: Research Focus
      text: >
        My work combines computational methods with biological insight to
        understand and ultimately treat inflammatory diseases.
      items:
        - name: Epigenomics
          icon: magnifying-glass
          description: >
            Mapping DNA methylation landscapes in immune and intestinal cells
            to identify disease-driving regulatory changes in IBD and RA.
        - name: Multi-omics Integration
          icon: circle-stack
          description: >
            Developing pipelines that fuse transcriptomics, proteomics,
            metabolomics and methylomics for a systems-level view of disease.
        - name: Bioinformatics Tool Development
          icon: code-bracket
          description: >
            Building open-source R/Python packages and reproducible workflows
            for the broader epigenomics community.
        - name: Translational Research
          icon: beaker
          description: >
            Bridging wet-lab discovery and clinical application — from
            biomarker identification to industry-ready assays.
        - name: Machine Learning
          icon: cpu-chip
          description: >
            Applying supervised and unsupervised learning to extract clinical
            patterns from high-dimensional omics data.
        - name: Industry Collaboration
          icon: building-office
          description: >
            Track record of academic–industry partnership (GlaxoSmithKline
            PhD, OmiQuant) translating research into practical solutions.

  # ── 4. FEATURED PUBLICATIONS ──────────────────────────────────────────────
  - block: collection
    id: featured-pubs
    content:
      title: Featured Publications
      subtitle: ''
      text: >
        Selected recent work. See the [full publication list](/publication/) for
        the complete record.
      filters:
        folders:
          - publication
        featured_only: true
    design:
      view: citation      # compact citation-style view
      columns: '1'

  # ── 5. RECENT PUBLICATIONS ────────────────────────────────────────────────
  - block: collection
    content:
      title: Recent Publications
      subtitle: ''
      filters:
        folders:
          - publication
        featured_only: false
        exclude_featured: true
      count: 5
    design:
      view: citation
      columns: '1'

  # ── 6. WORK EXPERIENCE ────────────────────────────────────────────────────
  - block: resume-experience
    id: experience
    content:
      username: admin
    design:
      date_format: January 2006
      is_education_first: false

  # ── 7. EDUCATION ──────────────────────────────────────────────────────────
  - block: resume-education
    content:
      username: admin

  # ── 8. SKILLS / TOOLS ─────────────────────────────────────────────────────
  - block: resume-skills
    id: skills
    content:
      title: Skills & Tools
      username: admin
    design:
      show_skill_percentage: false

  # ── 9. TEACHING (placeholder — add your courses) ─────────────────────────
  - block: markdown
    id: teaching
    content:
      title: Teaching
      text: |
        ### Current Courses
        - **Bioinformatics for Medical Sciences** — Amsterdam UMC (BSc/MSc)
        - **Epigenomics Data Analysis** — Guest lecture, Utrecht University

        ### Supervision
        Actively supervising BSc, MSc and PhD students in computational biology
        and bioinformatics projects. Interested candidates are welcome to
        [get in touch](/#contact).
    design:
      columns: '1'

  # ── 10. CONTACT ───────────────────────────────────────────────────────────
  - block: contact
    id: contact
    content:
      title: Contact
      text: >
        I welcome enquiries from prospective students, collaborators and industry
        partners. Feel free to reach out.
      email: a.y.li-yim@amsterdamumc.nl
      address:
        street: Meibergdreef 9
        city: Amsterdam
        postcode: '1105 AZ'
        country: Netherlands
        country_code: NL
      directions: Tytgat Institute, AMC building
      office_hours:
        - 'Monday–Friday 09:00–17:00 CET'
      appointment_url: ''
      contact_links: []
      autolink: true
      form:
        provider: ''   # Set to 'netlify' or 'formspree' if you want a web form
    design:
      columns: '2'
---
