

using System;
using System.Collections;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using System.Security.Policy;
using System.Security.Permissions;

using UnityEngine;
using UnityEngine.Networking;
using UnityEditor;
using UnityEditor.PackageManager;
using VRC.SDKBase;


namespace MikanDealer
{
	public class FrameSheet
	{
		public string ApiUrl;
		public string WebUrl;
		public string SheetKey;
		public string Worksheet;
	}

	public class PhotoItem
	{
		public enum TYPE { UNKNOWN, G_DRIVE, G_PHOTOS }

		public string PublicUrl;
		public string SrcUrl;
		public string ID;
		public string Title;
		public TYPE Type = TYPE.UNKNOWN;

		private PhotoItem() { }

		public static PhotoItem Parse(string id)
		{
			PhotoItem i = new PhotoItem() { ID = id };
			return i;
		}

		public static PhotoItem Parse(Dictionary<string, object> o)
		{
			if (o == null) return null;

			PhotoItem i = new PhotoItem();
			try
			{
				if (o.ContainsKey("public")) i.PublicUrl = (string)o["public"];
				if (o.ContainsKey("url")) i.SrcUrl = (string)o["url"];
				if (o.ContainsKey("id")) i.ID = (string)o["id"];
				if (o.ContainsKey("title")) i.Title = (string)o["title"];
				if (o.ContainsKey("type"))
				{
					if ((string)o["type"] == TYPE.G_PHOTOS.ToString()) i.Type = TYPE.G_PHOTOS;
					if ((string)o["type"] == TYPE.G_DRIVE.ToString()) i.Type = TYPE.G_DRIVE;
				}
				return i;
			}
			catch(Exception ex)
			{
				Debug.LogException(ex);
				return null;
			}
		}
	}

	[CustomEditor(typeof(SyncFrameManager))]
	public class MonoBehaviourModelEditor : Editor
	{
		private string API_URL = "https://sync-frame-api-65759203281.asia-northeast1.run.app/";
		private string WEB_URL = "https://sync-frame-web-65759203281.asia-northeast1.run.app/";
		SyncFrameManager _Instance = null;

		private FrameSheet CurrentSheet = null;
		private int PhotoLimit = 0;
		private int PhotoUsed = 0;
		private Dictionary<string, PhotoItem> PhotoTable = null;
		private IEnumerator Lock;
		private bool EditorIsFoldout = false;
		private string NewFrameId;

		private string TemporaryCacheSheet = null;

		void Awake()
		{
			EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
		}

		private void OnPlayModeStateChanged(PlayModeStateChange state)
		{
			if (state == PlayModeStateChange.ExitingEditMode || state == PlayModeStateChange.EnteredPlayMode)
			{
				ClearSyncFrames();
			}
		}

		void OnEnable()
		{
			_Instance = target as SyncFrameManager;
			LoadEnv();
			if (!String.IsNullOrEmpty(_Instance.CacheSheet)) ParseSheetJson(_Instance.CacheSheet);
		}

		void OnDisable()
		{
			if (!String.IsNullOrEmpty(TemporaryCacheSheet)) _Instance.CacheSheet = TemporaryCacheSheet;
		}

		public override void OnInspectorGUI()
		{
			//base.OnInspectorGUI();
			GUIStyle style = NormalStyle();
			GUIStyle bold = BoldStyle();

			EditorGUI.BeginDisabledGroup(Lock != null);
			{
				EditorGUILayout.LabelField("1. Spread Sheet URL には、次のようなスプレッドシートの URL を入力 (例) https://docs.google.com/spreadsheets/d/hoge/\n1列目をid、2列目を画像URL、3列目以降は自由です。", style);
				EditorGUILayout.LabelField("※ スプレッドシートの共有「リンクを知っている全員」「閲覧者」に必ずして下さい ※", bold);
				_Instance.SpreadSheetUrl = EditorGUILayout.TextField("Spread Sheet Url", _Instance.SpreadSheetUrl);
				EditorGUILayout.LabelField("");

				EditorGUILayout.LabelField("2. Work Sheet には、スプレッドシート下部のワークシート(タブ)の名前を入力", style);
				_Instance.WorkSheet = EditorGUILayout.TextField("Work Sheet", _Instance.WorkSheet);
				EditorGUILayout.LabelField("");

				EditorGUILayout.LabelField("3. スプレッドシートを読み込みます。", style);
				if (GUILayout.Button("読み込み！"))
				{
					LoadSheet();
					Lock = UpdatingSyncFrames(_Instance.SpreadSheetUrl, _Instance.WorkSheet);
					EditorCoroutine.Start(Lock);
				}
				EditorGUILayout.LabelField("");
			}
			EditorGUI.EndDisabledGroup();
			EditorGUI.BeginDisabledGroup(Lock != null || PhotoTable == null);
			{
				if (PhotoLimit > 0)
				{
					EditorGUILayout.LabelField("サーバーの画像使用量 " + PhotoUsed + "/" + PhotoLimit);
					EditorGUILayout.LabelField("");
				}
				EditorGUILayout.LabelField("4. 画像をサーバーにアップロードします。これには数分かかります。", style);
				if (GUILayout.Button("アップロード！"))
				{
					Lock = UploadingPhotos();
					EditorCoroutine.Start(Lock);
				}
				EditorGUILayout.LabelField("");

				EditorGUILayout.LabelField("5. 子オブジェクト Photo Frame を作成します。IDはスプレッドシート内のものを入力してください。", style);
				EditorGUILayout.LabelField("Photo Frame Manager は、この子オブジェクトだけの画像を管理します", style);
				NewFrameId = EditorGUILayout.TextField("Frame ID", NewFrameId);
				if (GUILayout.Button("作成") && !string.IsNullOrEmpty(NewFrameId))
				{
					MakeNewFrame(NewFrameId);
				}
				EditorGUILayout.LabelField("");
			}
			EditorGUI.EndDisabledGroup();

			{
				EditorGUILayout.LabelField("6. サーバーから画像を読み込み「仮表示」し、レイアウトを確認します。", style);
				EditorGUILayout.LabelField(" 確認ができれば「仮表示解除」します。", style);
				GUILayout.BeginHorizontal();
				{
					if (GUILayout.Button("仮表示"))
					{
						Lock = AssigningPhotos();
						EditorCoroutine.Start(Lock);
					}
					if (GUILayout.Button("仮表示解除"))
					{
						ClearSyncFrames();
					}
				}
				GUILayout.EndHorizontal();
				EditorGUILayout.LabelField("");

				EditorGUILayout.LabelField("7. ブラウザ上からも更新できます", style);
				string sheetKey = GetSpreadSheetKey(_Instance.SpreadSheetUrl);
				string url = WEB_URL + "?key=" + sheetKey + "&worksheet=" + _Instance.WorkSheet;
				if (GUILayout.Button("開く"))
				{
					System.Diagnostics.Process.Start(url);
				}
			}

			EditorIsFoldout = EditorGUILayout.Foldout(EditorIsFoldout, "危険な操作");
			if (EditorIsFoldout)
			{
				EditorGUI.BeginDisabledGroup(Lock != null || PhotoTable == null);
				{
					GUIStyle red = StartColorStyle(Color.red);
					GUILayout.Label("現在のワークシート(タブ)の画像を削除する際は、その名前を入力し、削除ボタンを押してください。", red);
					EndColorStyle(red);
					_Instance.RemovingSheet = EditorGUILayout.TextField("Removing Sheet", _Instance.RemovingSheet);
					if (GUILayout.Button("削除"))
					{
						Lock = RemovingPhotos(_Instance.SpreadSheetUrl, _Instance.WorkSheet, _Instance.RemovingSheet);
						EditorCoroutine.Start(Lock);
					}
				}
				EditorGUI.EndDisabledGroup();
			}
		}

		private GUIStyle NormalStyle()
		{
			GUIStyle style = new GUIStyle(GUI.skin.label);
			style.wordWrap = true;
			return style;
		}
		private GUIStyle BoldStyle()
		{
			GUIStyle bold = new GUIStyle(GUI.skin.label);
			bold.wordWrap = true;
			bold.fontStyle = FontStyle.Bold;
			return bold;			
		}
		private GUIStyle StartColorStyle(Color color)
		{
			GUIStyle style = GUI.skin.label;
			GUIStyleState styleState = new GUIStyleState();
			styleState.textColor = color;
			style.normal = styleState;
			return style;
		}
		private void EndColorStyle(GUIStyle style)
		{
			GUIStyleState styleState2 = new GUIStyleState();
			styleState2.textColor = EditorStyles.label.normal.textColor;
			style.normal = styleState2;
		}

		private string GetSpreadSheetKey(string url)
		{
			Match match = Regex.Match(url, "https://docs.google.com/spreadsheets/d/([a-zA-Z0-9_-]+)/");
			if (match.Success) return match.Groups[1].Value;

			Debug.LogError("スプレッドシートのURLを入力してください (例) https://docs.google.com/spreadsheets/d/hoge/");
			return null;
		}

		private bool Validate(string key, string worksheet)
		{
			if (string.IsNullOrEmpty(worksheet))
			{
				Debug.LogError("ワークシートが入力されていません");
				return false;
			}
			return true;
		}

		private IEnumerator UpdatingSyncFrames(string url, string worksheet)
		{
			string key = GetSpreadSheetKey(url);
			if (string.IsNullOrEmpty(key) || !Validate(key, worksheet))
			{
				Debug.LogError("スプレッドシートのURLを確認してください " + url);
				Lock = null;
				yield break;
			}

			foreach (var frame in SelectSyncFrames()) frame.AssignLoading();

			string api = API_URL + "sheet/" + key + "/" + worksheet + ".json";
			using (UnityWebRequest www = UnityWebRequest.Get(api))
			{
				yield return www.SendWebRequest();
				while (!www.isDone) yield return null;
				if (www.result != UnityWebRequest.Result.Success)
				{
					Debug.LogError("Sheet API: " + api + "\n" + www.error);
					Lock = null;
					yield break;
				}
				Dictionary<string, object> response = Json.Deserialize(www.downloadHandler.text) as Dictionary<string, object>;
				if (response == null || (string)response["status"] != "OK" || response["frame"] == null)
				{
					Debug.LogError("スプレッドシートからデータの読み込みに失敗しました\n" + www.downloadHandler.text);
					Lock = null;
					yield break;
				}
				ParseSheetJson(www.downloadHandler.text);
				TemporaryCacheSheet = www.downloadHandler.text;
			}
			Debug.Log("読み込み完了！");
			Lock = null;
		}

		private void ParseSheetJson(string content)
		{
			Dictionary<string, object> response = Json.Deserialize(content) as Dictionary<string, object>;

			Dictionary<string, object> frame = response["frame"] as Dictionary<string, object>;
			if (frame == null) return;
			PhotoLimit = int.Parse(frame["limit"].ToString());
			PhotoUsed = int.Parse(frame["used"].ToString());

			PhotoTable = new Dictionary<string, PhotoItem>();
			foreach (var o in response["items"] as List<object>)
			{
				var item = PhotoItem.Parse(o as Dictionary<string, object>);
				if (item != null) PhotoTable[item.ID] = item;
			}
		}

		private IEnumerator UploadingPhotos()
		{
			foreach(PhotoItem item in PhotoTable.Values)
			{
				double start = EditorApplication.timeSinceStartup;
				while(EditorApplication.timeSinceStartup - start < 3.0) yield return new WaitForSeconds(1f);
				string key = CurrentSheet.SheetKey;
				string worksheet = CurrentSheet.Worksheet;
				string api = API_URL + "upload/" + key + "/" + worksheet + "/" + item.ID;
				using (UnityWebRequest www = UnityWebRequest.Get(api))
				{
					yield return www.SendWebRequest();
					while (!www.isDone) yield return null;
					if (www.result != UnityWebRequest.Result.Success)
					{
						Debug.LogError(api + " " + www.error);
						continue;
					}
					Debug.Log("Uploaded=" + api);
				}
			}
			Debug.Log("アップロード完了！");
			Lock = null;
		}

		private IEnumerator AssigningPhotos()
		{
			foreach(var frame in SelectSyncFrames())
			{
				EditorCoroutine.Start(AssigningWebTexture(frame));

				double start = EditorApplication.timeSinceStartup;
				while(EditorApplication.timeSinceStartup - start < 1.0) yield return new WaitForSeconds(1f);
			}
			Lock = null;
		}

		private IEnumerator RemovingPhotos(string url, string worksheet, string removing)
		{
			if (removing != worksheet)
			{
				Debug.LogError("ワークシート名が一致しません " + worksheet);
				Lock = null;
				yield break;
			}
			string key = GetSpreadSheetKey(url);
			if (string.IsNullOrEmpty(key) || !Validate(key, worksheet))
			{
				Debug.LogError("スプレッドシートのURLを確認してください " + url);
				Lock = null;
				yield break;
			}

			string api = API_URL + "delete/" + key + "/" + worksheet;
			using (UnityWebRequest www = UnityWebRequest.Get(api))
			{
				yield return www.SendWebRequest();
				while (!www.isDone) yield return null;
				if (www.result != UnityWebRequest.Result.Success)
				{
					Debug.LogError(www.error);
					yield break;
				}
				string[] lines = www.downloadHandler.text.Split('\n');
				if (lines[0] != "OK" && lines.Length > 1)
				{
					Debug.LogError(lines[1]);
				}
			}
			Debug.Log("削除完了");
			Lock = null;
		}

		private SyncFrame[] SelectSyncFrames()
		{
			if (_Instance == null) return new SyncFrame[] { };

			var frames = _Instance.transform.GetComponentsInChildren<SyncFrame>();
			foreach (var frame in frames)
			{
				if (string.IsNullOrEmpty(frame.ID)) continue;
			}
			return frames;
		}

		private IEnumerator AssigningWebTexture(SyncFrame frame)
		{
			PhotoItem item;
			if (PhotoTable != null && PhotoTable.ContainsKey(frame.ID))
			{
				item = PhotoTable[frame.ID];
				frame.Url = new VRCUrl(item.PublicUrl);
			}

			Renderer renderer = frame.GetComponent<Renderer>();
			if (renderer == null || renderer.sharedMaterial == null) yield break;

			using (UnityWebRequest www = UnityWebRequestTexture.GetTexture(frame.Url.Get()))
			{
				yield return www.SendWebRequest();
				while (!www.isDone) yield return null;
				if (www.result != UnityWebRequest.Result.Success)
				{
					Debug.LogError("Image URL: " + frame.Url.Get() + "\n" + www.error);
				}
				else
				{
					Material copied = new Material(renderer.sharedMaterial);
					Texture2D tex = ((DownloadHandlerTexture)www.downloadHandler).texture;
					copied.mainTexture = tex;
					renderer.sharedMaterial = copied;
					if (frame.AutoAdjustAspect)
						frame.AdjustTexture(tex, 2);
					else
						frame.DoneTexture(tex, 2);
				}
			}
		}

		private void ClearSyncFrames()
		{
			foreach(var frame in SelectSyncFrames())
			{
				ClearTexture(frame);
			}
		}

		private void ClearTexture(SyncFrame frame)
		{
			Renderer renderer = frame.GetComponent<Renderer>();
			if (renderer == null || renderer.sharedMaterial == null) return;

			renderer.sharedMaterial.mainTexture = null;
		}

		private void LoadEnv()
		{
			string path = System.IO.Path.Combine(Application.dataPath, "MikanDealer/SyncFrame/env.json");
			if (System.IO.File.Exists(path))
			{
				var data = Json.Deserialize(System.IO.File.ReadAllText(path)) as Dictionary<string, object>;
				if (!string.IsNullOrEmpty(data["API_URL"] as string))
				{
					API_URL = data["API_URL"] as string;
					Debug.Log("API_URL is overwritten :" + API_URL);
				}
				if (!string.IsNullOrEmpty(data["WEB_URL"] as string))
				{
					WEB_URL = data["WEB_URL"] as string;
					Debug.Log("WEB_URL is overwritten :" + WEB_URL);
				}
			}
		}

		private void LoadSheet()
		{
			CurrentSheet = new FrameSheet()
			{
				ApiUrl = API_URL.EndsWith("/") ? API_URL : API_URL + "/",
				WebUrl = WEB_URL.EndsWith("/") ? WEB_URL : WEB_URL + "/",
				SheetKey = GetSpreadSheetKey(_Instance.SpreadSheetUrl),
				Worksheet = _Instance.WorkSheet
			};
		}

		private void MakeNewFrame(string id)
		{
			GameObject selected = Selection.activeGameObject;
			if (selected == null || selected.GetComponent<SyncFrameManager>() == null) return;

			GameObject newFrame = GameObject.CreatePrimitive(PrimitiveType.Quad);
			newFrame.name = id;
			newFrame.transform.parent = selected.transform;
			newFrame.transform.localPosition = new Vector3(0, 0, 0);
			newFrame.GetComponent<Renderer>().material = new Material(Shader.Find("MikanDealer/SyncFrame"));

			Debug.Log(PhotoTable[id]);
			var component = newFrame.AddComponent<SyncFrame>();
			component.ID = id;
			if (PhotoTable != null && PhotoTable.ContainsKey(id))
			{
				PhotoItem item = PhotoTable[id];
				component.Url = new VRCUrl(item.PublicUrl);
			}
		}
	}
}