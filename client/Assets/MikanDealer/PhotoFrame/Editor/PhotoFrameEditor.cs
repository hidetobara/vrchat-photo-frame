
using UnityEngine;
using VRC.SDKBase;

using UnityEditor;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using UnityEditor.PackageManager;

namespace MikanDealer
{
	[CustomEditor(typeof(PhotoFrameManager))]
	public class MonoBehaviourModelEditor : Editor
	{
		PhotoFrameManager _Instance = null;

		private string BASE_URL = "https://photoframe-a3miq2wxma-an.a.run.app/";
		private Dictionary<string, object> PhotoTable = null;


		void OnEnable()
		{
			_Instance = target as PhotoFrameManager;
		}

		public override void OnInspectorGUI()
		{
			base.OnInspectorGUI();

			EditorGUILayout.LabelField("スプレッドシートから読み込み");
			using (new EditorGUILayout.HorizontalScope())
			{
				if (GUILayout.Button("更新＆お試し表示"))
					EditorCoroutine.Start(UpdatingPhotoFrames(_Instance.SpreadSheetKey, _Instance.WorkSheet));
				if (GUILayout.Button("クリア"))
					ClearingPhotoFrames();

			}

		}

		private IEnumerator UpdatingPhotoFrames(string key, string worksheet)
		{
			if (!Validate(key, worksheet)) yield break;
			EditorCoroutine.Start(GettingPhotoTable(key, worksheet));
			int life = 0;
			while(PhotoTable == null)
			{
				if (life > 1000) break;
				yield return new WaitForSecondsRealtime(1f);
				life++;
			}
			if (PhotoTable == null)
			{
				Debug.LogError("スプレッドシートからデータの読み込みに失敗しました");
				yield break;
			}
			foreach(var frame in SelectPhotoFrames())
			{
				EditorCoroutine.Start(AssigningWebTexture(frame));
				yield return new WaitForSecondsRealtime(1f);
			}
		}

		private void ClearingPhotoFrames()
		{
			foreach(var frame in SelectPhotoFrames())
			{
				ClearTexture(frame);
			}
		}

		private bool Validate(string key, string worksheet)
		{
			if (string.IsNullOrEmpty(key))
			{
				Debug.LogError("スプレッドシートのキーが入力されていません");
				return false;
			}
			if (string.IsNullOrEmpty(worksheet))
			{
				Debug.LogError("ワークシートが入力されていません");
				return false;
			}
			return true;
		}

		private IEnumerator GettingPhotoTable(string key, string worksheet)
		{
			string url = BASE_URL + "sheet/" + key + "/" + worksheet + ".json";
			Debug.Log(url);
			using (UnityWebRequest www = UnityWebRequest.Get(url))
			{
				yield return www.SendWebRequest();
				while (!www.isDone) yield return null;
				if (www.isHttpError || www.isNetworkError)
				{
					Debug.LogError(www.error);
					yield break;
				}
				else
				{
					string[] lines = www.downloadHandler.text.Split('\n');
					if (lines[0] != "OK")
					{
						Debug.LogError(lines[1]);
						yield break;
					}
					PhotoTable = new Dictionary<string, object>();
					foreach (var o in Json.Deserialize(lines[1]) as List<object>)
					{
						Debug.Log(o);
						var box = o as Dictionary<string, object>;
						if (box.ContainsKey("name") && !string.IsNullOrEmpty((string)box["name"])) PhotoTable[(string)box["name"]] = box;
					}
					Debug.Log(lines[1]);
					Debug.Log(PhotoTable);
				}
			}
		}

		private PhotoFrame[] SelectPhotoFrames()
		{
			var frames = _Instance.transform.GetComponentsInChildren<PhotoFrame>();
			foreach (var frame in frames)
			{
				if (string.IsNullOrEmpty(frame.Name)) frame.Name = frame.gameObject.name;
			}
			return frames;
		}

		private IEnumerator AssigningWebTexture(PhotoFrame frame)
		{
			if (PhotoTable.ContainsKey(frame.Name))
			{
				var box = PhotoTable[frame.Name] as Dictionary<string, object>;
				frame.Url = new VRCUrl(box["url"] as string);
			}
			else
			{
				frame.Url = null;
				yield break;
			}

			string url = frame.Url.Get();
			if (url == null) yield break;
			Debug.Log(url);

			Renderer renderer = frame.GetComponent<Renderer>();
			if (renderer == null || renderer.sharedMaterial == null) yield break;

			using (UnityWebRequest www = UnityWebRequestTexture.GetTexture(url))
			{
				yield return www.SendWebRequest();
				while (!www.isDone) yield return null;
				if (www.isHttpError || www.isNetworkError)
				{
					Debug.LogError(www.error);
				}
				else
				{
					Material copied = new Material(renderer.sharedMaterial);
					copied.mainTexture = ((DownloadHandlerTexture)www.downloadHandler).texture;
					renderer.sharedMaterial = copied;
				}
			}
		}

		private void ClearTexture(PhotoFrame frame)
		{
			frame.Url = null;
			Renderer renderer = frame.GetComponent<Renderer>();
			if (renderer == null || renderer.sharedMaterial == null) return;

			renderer.sharedMaterial.mainTexture = null;
		}
	}
}