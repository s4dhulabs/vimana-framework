from .show import Show

class TestReporter:
    def __init__(self, verbose=False, colors_disabled=False):
        self.show = Show(silent_mode=not verbose, colors_disabled=colors_disabled)
        self.verbose = verbose
        self.current_phase = None

    def start_testing_session(self, target_url, models_count, testable_models):
        self.show.show_test_phase_header("Pydantic Testing Session", [
            f"Target URL: {target_url}",
            f"Total Models Found: {models_count}",
            f"Testable Models: {testable_models}"
        ])

    def start_model_testing(self, model_name, test_count):
        if self.verbose:
            self.show.show_operation_header(f"Testing Model: {model_name}")
        else:
            print(f" → Testing model: {model_name}")

    def report_test_progress(self, model_name, current, total):
        if self.verbose:
            self.show.show_test_progress(model_name, current, total)

    def show_request_response(self, method, path, version, headers, body, response, response_text):
        if self.verbose:
            self.show.show_request_info(method, path, version, headers, body)
            self.show.show_response_info(response, response_text)

    def show_test_summary(self, results):
        self.show.show_test_phase_header("Test Results Summary", [
            f"Total Tests: {results['total']}",
            f"Passed: {results['passed']}",
            f"Failed: {results['failed']}",
            f"Coverage: {results['coverage']}%"
        ]) 