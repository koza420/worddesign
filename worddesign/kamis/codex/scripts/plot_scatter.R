#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: plot_scatter.R <metrics_csv> <output_dir> [target_size] [fingerprint_csv]")
}

metrics_csv <- args[[1]]
output_dir <- args[[2]]
target_size <- ifelse(length(args) >= 3, as.integer(args[[3]]), 136L)
fingerprint_csv <- ifelse(length(args) >= 4, args[[4]], Sys.getenv("FINGERPRINT_CSV", ""))

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

d <- read.csv(metrics_csv, stringsAsFactors = FALSE)
if (nrow(d) == 0) {
  stop("metrics CSV is empty")
}

d <- d[d$selected_size >= target_size, ]
if (nrow(d) == 0) {
  stop(paste0("No rows with selected_size >= ", target_size))
}

fp_points <- NULL
if (nzchar(fingerprint_csv)) {
  if (!file.exists(fingerprint_csv)) {
    warning(sprintf("fingerprint CSV not found: %s", fingerprint_csv))
  } else {
    f <- read.csv(fingerprint_csv, stringsAsFactors = FALSE)
    if ("subset_len_recomputed" %in% names(f)) {
      f <- f[f$subset_len_recomputed >= target_size, ]
    }

    if (all(c("A", "C", "G", "T") %in% names(f))) {
      sorted_counts <- t(apply(f[, c("A", "C", "G", "T")], 1, sort))
      fp_points <- unique(data.frame(x = sorted_counts[, 1], y = sorted_counts[, 2]))
    } else if (all(c("count_min1", "count_min2") %in% names(f))) {
      fp_points <- unique(data.frame(x = f$count_min1, y = f$count_min2))
    } else {
      warning("fingerprint CSV did not have expected columns (A,C,G,T) or (count_min1,count_min2)")
    }
  }
}

num_zeros <- d$count_min1
num_ones <- d$count_min2
minimal_sums <- d$min_sum
configs <- if ("config" %in% names(d)) d$config else rep("unknown", nrow(d))
is_social <- grepl("social", configs, ignore.case = TRUE)
is_online <- grepl("online", configs, ignore.case = TRUE)
is_standard <- !(is_social | is_online)
# Standard: circle (pch 21), Social: square (pch 22), Online: triangle (pch 24)
pch_by_config <- ifelse(is_social, 22, ifelse(is_online, 24, 21))

mean_a_std <- if (any(is_standard)) mean(d$a_count[is_standard]) else NA_real_
mean_c_std <- if (any(is_standard)) mean(d$c_count[is_standard]) else NA_real_
mean_a_soc <- if (any(is_social)) mean(d$a_count[is_social]) else NA_real_
mean_c_soc <- if (any(is_social)) mean(d$c_count[is_social]) else NA_real_
mean_a_onl <- if (any(is_online)) mean(d$a_count[is_online]) else NA_real_
mean_c_onl <- if (any(is_online)) mean(d$c_count[is_online]) else NA_real_

# Viridis-like palette for better contrast/readability.
pal <- grDevices::hcl.colors(100, "viridis")
map_color <- function(values) {
  idx <- as.integer(cut(values, breaks = 100, include.lowest = TRUE))
  pal[idx]
}
cols <- map_color(minimal_sums)

legend_vals <- sort(unique(minimal_sums))
legend_cols <- map_color(legend_vals)

plot1 <- file.path(output_dir, sprintf("scatter_min_sum_size_ge_%d.png", target_size))
png(plot1, width = 1400, height = 1000, res = 130)
plot(
  num_zeros,
  num_ones,
  col = "#2A2A2A",
  pch = pch_by_config,
  bg = cols,
  lwd = 0.7,
  cex = 1.75,
  xlab = "Smallest base count among A/C/G/T",
  ylab = "Second-smallest base count among A/C/G/T",
  main = sprintf("Scatter of solutions (size >= %d), colored by min_sum", target_size)
)
grid(col = "#CCCCCC", lwd = 0.8)
if (!is.null(fp_points) && nrow(fp_points) > 0) {
  points(fp_points$x, fp_points$y, pch = 4, col = "black", cex = 1.75, lwd = 2.5)
  fp_labels <- sprintf("(%d,%d)", as.integer(round(fp_points$x)), as.integer(round(fp_points$y)))
  text(fp_points$x, fp_points$y, labels = fp_labels, pos = 4, offset = 0.6, cex = 0.9, col = "black")
}
legend(
  "topright",
  legend = paste0("min_sum=", legend_vals),
  col = legend_cols,
  pch = 19,
  cex = 0.8,
  bg = "white"
)
shape_legend <- character(0)
shape_pch <- integer(0)
shape_lwd <- numeric(0)
if (any(is_standard)) {
  shape_legend <- c(shape_legend, sprintf("Standard (mean A=%.1f, C=%.1f)", mean_a_std, mean_c_std))
  shape_pch <- c(shape_pch, 21)
  shape_lwd <- c(shape_lwd, 1.0)
}
if (any(is_social)) {
  shape_legend <- c(shape_legend, sprintf("Social (mean A=%.1f, C=%.1f)", mean_a_soc, mean_c_soc))
  shape_pch <- c(shape_pch, 22)
  shape_lwd <- c(shape_lwd, 1.0)
}
if (any(is_online)) {
  shape_legend <- c(shape_legend, sprintf("Online (mean A=%.1f, C=%.1f)", mean_a_onl, mean_c_onl))
  shape_pch <- c(shape_pch, 24)
  shape_lwd <- c(shape_lwd, 1.0)
}
if (!is.null(fp_points) && nrow(fp_points) > 0) {
  shape_legend <- c(shape_legend, "LLM heuristic")
  shape_pch <- c(shape_pch, 4)
  shape_lwd <- c(shape_lwd, 2.5)
}
if (length(shape_legend) > 0) {
  legend(
    "bottomleft",
    legend = shape_legend,
    pch = shape_pch,
    pt.bg = "white",
    col = "#2A2A2A",
    pt.cex = 1.1,
    pt.lwd = shape_lwd,
    cex = 0.9,
    bg = "white"
  )
}
dev.off()

plot2 <- file.path(output_dir, sprintf("scatter_136_style_size_ge_%d.png", target_size))
png(plot2, width = 1400, height = 1100, res = 130)
old_par <- par(no.readonly = TRUE)
layout(matrix(c(1, 2), nrow = 1), widths = c(5.3, 0.7))
par(
  mar = c(5.2, 5.2, 4.4, 1.2),
  bg = "#E6E6E6",
  cex.axis = 1.05,
  cex.lab = 1.2,
  cex.main = 1.25
)
plot(
  num_zeros,
  num_ones,
  col = "#2A2A2A",
  pch = pch_by_config,
  bg = cols,
  cex = 1.8,
  lwd = 0.8,
  xlab = "Number of As",
  ylab = "Number of Cs",
  main = sprintf("Scatter plot of solutions by composition, sum and weight (size >= %d)", target_size),
  xlim = c(170, 280),
  ylim = c(170, 280),
  xaxt = "n",
  yaxt = "n"
)
axis(1, at = seq(180, 280, by = 20))
axis(2, at = seq(180, 280, by = 20), las = 1)
grid(col = "#A9A9A9", lwd = 0.8)
if (!is.null(fp_points) && nrow(fp_points) > 0) {
  points(fp_points$x, fp_points$y, pch = 4, col = "black", cex = 1.8, lwd = 2.6)
  fp_labels <- sprintf("(%d,%d)", as.integer(round(fp_points$x)), as.integer(round(fp_points$y)))
  text(fp_points$x, fp_points$y, labels = fp_labels, pos = 4, offset = 0.6, cex = 0.9, col = "black")
}
if (length(shape_legend) > 0) {
  legend(
    "bottomleft",
    legend = shape_legend,
    pch = shape_pch,
    pt.bg = "white",
    col = "#2A2A2A",
    pt.cex = 1.1,
    pt.lwd = shape_lwd,
    cex = 0.9,
    bg = "white"
  )
}

x <- seq(0, 544, length.out = 100)
lines(x, x, col = "red", lty = 2, lwd = 1.3)
lines(x, 544 - x, col = "red", lty = 2, lwd = 1.3)
abline(h = 272, v = 272, col = "red", lty = 2, lwd = 1.3)

text(215, 275, "|C|>|G|", cex = 1.15)
text(215, 268, "|C|<|G|", cex = 1.15)
text(200, 205, "|A|<|C|", srt = 45, cex = 1.15)
text(204, 201, "|A|>|C|", srt = 45, cex = 1.15)
text(273, 200, "|A|>|T|", srt = 90, cex = 1.15)
text(268, 200, "|A|<|T|", srt = 90, cex = 1.15)

# Multiplicity labels for repeated (x,y) points.
pt <- paste(num_zeros, num_ones, sep = ",")
tab <- table(pt)
for (name in names(tab)) {
  count <- as.integer(tab[[name]])
  if (count > 1) {
    xy <- strsplit(name, ",", fixed = TRUE)[[1]]
    xval <- as.numeric(xy[[1]])
    yval <- as.numeric(xy[[2]])
    text(xval, yval, labels = as.character(count), col = "red", cex = 1.0, font = 2)
  }
}

# Draw a continuous colorbar.
par(mar = c(5.2, 0.1, 4.4, 2.8), bg = "#E6E6E6")
plot.new()
ymin <- min(minimal_sums)
ymax <- max(minimal_sums)
plot.window(xlim = c(0, 1), ylim = c(ymin, ymax))
ybreaks <- seq(ymin, ymax, length.out = length(pal) + 1)
for (i in seq_along(pal)) {
  rect(0, ybreaks[i], 1, ybreaks[i + 1], col = pal[i], border = NA)
}
axis(4, at = seq(ymin, ymax, by = 1), las = 1, cex.axis = 0.95)
mtext("Minimal Sum", side = 4, line = 2.1, cex = 1.0)
box()

par(old_par)
dev.off()

cat("Wrote plots:\n")
cat("  ", plot1, "\n")
cat("  ", plot2, "\n")
if (!is.null(fp_points) && nrow(fp_points) > 0) {
  cat("LLM heuristic classes overlaid as crosses:", nrow(fp_points), "\n")
}
