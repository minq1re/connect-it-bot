import 'package:flutter/material.dart';

import '../core/strings.dart';
import '../services/api_service.dart';

class ReportDialog extends StatefulWidget {
  const ReportDialog({
    super.key,
    required this.apiService,
    required this.reportedUserId,
  });

  final ApiService apiService;
  final int reportedUserId;

  @override
  State<ReportDialog> createState() => _ReportDialogState();
}

class _ReportDialogState extends State<ReportDialog> {
  static const Color _bgColor = Color(0xFFBEE3DB);
  static const Color _textColor = Color(0xFF555B6E);

  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _controller = TextEditingController();
  final RequestCancelToken _cancelToken = RequestCancelToken();
  bool _submitting = false;
  String? _serverError;

  @override
  void dispose() {
    if (_submitting) {
      _cancelToken.cancel();
    }
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_submitting) return;
    setState(() {
      _serverError = null;
    });
    if (!_formKey.currentState!.validate()) return;

    setState(() => _submitting = true);
    try {
      await widget.apiService.reportUser(
        widget.reportedUserId,
        _controller.text.trim(),
        cancelToken: _cancelToken,
      );
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.statusCode == 499 || e.message == 'request_cancelled') {
        return;
      }
      setState(() {
        _serverError = e.statusCode == 409 ? Strings.reportDuplicate : e.message;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _serverError = Strings.reportErrorGeneric);
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final Size size = MediaQuery.sizeOf(context);
    final bool narrow = size.width < 420;
    final double dialogWidth = (size.width * 0.9).clamp(280, 400).toDouble();
    final double maxHeight = size.height * 0.7;

    return Dialog(
      backgroundColor: _bgColor,
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: dialogWidth, maxHeight: maxHeight),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Text(
                  Strings.reportTitle,
                  style: TextStyle(
                    color: _textColor,
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _controller,
                  minLines: 4,
                  maxLines: 7,
                  maxLength: 500,
                  enabled: !_submitting,
                  decoration: InputDecoration(
                    hintText: Strings.reportHint,
                    filled: true,
                    fillColor: Colors.white.withValues(alpha: 0.75),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: BorderSide.none,
                    ),
                  ),
                  validator: (String? value) {
                    final String text = (value ?? '').trim();
                    if (text.isEmpty) return Strings.reportValidationEmpty;
                    if (text.length < 10) return Strings.reportValidationMin;
                    if (text.length > 500) return Strings.reportValidationMax;
                    return null;
                  },
                ),
                if (_serverError != null) ...<Widget>[
                  const SizedBox(height: 6),
                  Text(
                    _serverError!,
                    style: const TextStyle(color: Colors.red, fontSize: 13),
                  ),
                ],
                const SizedBox(height: 10),
                if (narrow)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: _actionButtons(narrow: true),
                  )
                else
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: _actionButtons(narrow: false),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  List<Widget> _actionButtons({required bool narrow}) {
    final Widget cancelBtn = OutlinedButton(
      onPressed: _submitting ? null : () => Navigator.of(context).pop(false),
      child: const Text(Strings.cancel),
    );
    final Widget submitBtn = ElevatedButton(
      onPressed: _submitting ? null : _submit,
      child: _submitting
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Text(Strings.send),
    );
    if (narrow) {
      return <Widget>[
        cancelBtn,
        const SizedBox(height: 8),
        submitBtn,
      ];
    }
    return <Widget>[
      cancelBtn,
      const SizedBox(width: 10),
      submitBtn,
    ];
  }
}
