/*
 * SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION.
 * SPDX-License-Identifier: Apache-2.0
 */

#include <rmm/logger.hpp>

#include <cstdlib>
#include <memory>
#include <string>

namespace rmm {

rapids_logger::sink_ptr default_sink()
{
#ifdef _MSC_VER
  char* filename = nullptr;
  size_t len = 0;
  _dupenv_s(&filename, &len, "RMM_DEBUG_LOG_FILE");
#else
  auto* filename = std::getenv("RMM_DEBUG_LOG_FILE");
#endif
  if (filename != nullptr) {
    auto sink = std::make_shared<rapids_logger::basic_file_sink_mt>(filename, true);
#ifdef _MSC_VER
    std::free(filename);
#endif
    return sink;
  }
  return std::make_shared<rapids_logger::stderr_sink_mt>();
}

std::string default_pattern() { return "[%6t][%H:%M:%S:%f][%-6l] %v"; }

rapids_logger::logger& default_logger()
{
  static rapids_logger::logger logger_ = [] {
    rapids_logger::logger l{"RMM", {default_sink()}};
    l.set_pattern(default_pattern());
    return l;
  }();
  return logger_;
}

}  // namespace rmm
